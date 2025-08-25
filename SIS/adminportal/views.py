from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.db.models import Q
from django.http import HttpResponse
from accounts.decorators import role_required
from accounts.models import CustomUser
from .forms import (
    LecturerCreationForm, StudentUpdateForm, StudentProfileUpdateForm,
    CourseForm, DepartmentForm, AddStudentForm, AssignLecturersToClassGroupForm,
    ClassGroupForm, SubjectForm
)
from core.models import Department, Course, Lecturer, Student, Enrollment, ClassGroup
import csv
from django.template.loader import render_to_string
from .forms import CustomUserCreationForm
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Q, Sum, Count
from django.utils import timezone
from accounts.decorators import role_required
from accounts.models import CustomUser
from core.models import Student, StudentFeePlan, StudentFeeInstallment
from .forms import FeePlanCreateForm, FeePlanCreateForStudentForm, InstallmentUpdateForm

# ---------- LECTURERS ----------

def lecturer_list(request):
    query = request.GET.get('q', '')
    department_id = request.GET.get('department')

    lecturers = Lecturer.objects.select_related('user', 'department').prefetch_related('subjects', 'classgroups')

    if query:
        lecturers = lecturers.filter(
            Q(user__full_name__icontains=query) |
            Q(user__short_name__icontains=query) |
            Q(user__email__icontains=query)
        )
    if department_id:
        lecturers = lecturers.filter(department_id=department_id)

    departments = Department.objects.all()
    return render(request, 'adminportal/lecturer_part/lecturer_list.html', {
        'lecturers': lecturers,
        'departments': departments,
    })

@role_required(CustomUser.Role.ADMIN)
def add_lecturer(request):
    if request.method == 'POST':
        form = LecturerCreationForm(request.POST, request.FILES)
        if form.is_valid():
            lecturer = form.save(commit=False)
            lecturer.role = CustomUser.Role.LECTURER
            lecturer.save()
            form.save_m2m()
            messages.success(request, "Lecturer added successfully.", extra_tags='lecturer')
            return redirect('adminportal:lecturer_list')
        else:
            messages.error(request, "Please correct the errors in the lecturer form.", extra_tags='lecturer')
    else:
        form = LecturerCreationForm()
    return render(request, 'adminportal/lecturer_part/add_lecturer.html', {
        'lecturer_form': form,
        'departments': Department.objects.all(),
        'courses': Course.objects.all(),
    })

def export_lecturers(request):
    lecturers = Lecturer.objects.select_related('user__department').prefetch_related('classgroups')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="lecturers.csv"'

    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Phone', 'Department', 'Class Groups'])
    for lecturer in lecturers:
        user = lecturer.user
        name = user.get_full_name()
        email = user.email
        phone = user.phone_number or "-"
        department = user.department.name if user.department else "-"
        class_groups = ', '.join([cg.name for cg in lecturer.classgroups.all()])
        writer.writerow([name, email, phone, department, class_groups])

    return response

# ---------- STUDENTS ----------

@role_required(CustomUser.Role.ADMIN)
def student_list(request):
    students = CustomUser.objects.filter(role=CustomUser.Role.STUDENT).select_related('department').order_by('full_name')

    # GET parameters for filtering
    department_id = request.GET.get('department')
    classgroup_id = request.GET.get('classgroup')
    query = request.GET.get('q', '').strip()  # <-- search query

    # Filter by department
    if department_id:
        students = students.filter(department_id=department_id)

    # Filter by class group (through Enrollment relationship)
    if classgroup_id:
        students = students.filter(student__enrollment__class_group_id=classgroup_id).distinct()

    # Search by name or email
    if query:
        students = students.filter(
            Q(full_name__icontains=query) |
            Q(short_name__icontains=query) |
            Q(email__icontains=query)
        )

    # Get filter dropdown values
    departments = Department.objects.all()
    classgroups = ClassGroup.objects.all()

    return render(request, 'adminportal/student_part/student_list.html', {
        'students': students,
        'departments': departments,
        'classgroups': classgroups,
    })


@role_required(CustomUser.Role.ADMIN)
def add_student(request):
    if request.method == "POST":
        form = AddStudentForm(request.POST, request.FILES)
        if form.is_valid():
            data = form.cleaned_data

            # Check for duplicates
            if CustomUser.objects.filter(email=data['email']).exists():
                form.add_error('email', "A user with this email already exists.")
            elif CustomUser.objects.filter(identity_card_number=data['identity_card_number']).exists():
                form.add_error('identity_card_number', "A user with this IC number already exists.")
            else:
                # Create the user
                password = data['password'] or 'password123'
                user = CustomUser.objects.create_user(
                    email=data['email'],
                    password=password,
                    identity_card_number=data['identity_card_number'],
                    full_name=data['full_name'],
                    short_name=data.get('short_name') or data['full_name'].split()[0],
                    role=CustomUser.Role.STUDENT,
                    phone_number=data.get('phone_number'),
                    address=data.get('address'),
                    department=data['department'],
                )
                if data.get('profile_picture'):
                    user.profile_picture = data['profile_picture']
                    user.save(update_fields=['profile_picture'])

                # Get the created student profile (via signal)
                student = Student.objects.get(user=user)
                student.date_of_birth = data.get('date_of_birth')
                student.class_group = data['class_group']
                student.emergency_name = data.get('emergency_name')
                student.emergency_relation = data.get('emergency_relation')
                student.emergency_phone = data.get('emergency_phone')
                student.save()

                # Create enrollment record
                Enrollment.objects.create(student=student, class_group=data['class_group'])

                messages.success(request, f"Student {user.full_name} added and enrolled successfully.")
                return redirect('adminportal:student_list')
    else:
        form = AddStudentForm()

    return render(request, 'adminportal/student_part/add_student.html', {'form': form})

@role_required(CustomUser.Role.ADMIN)
def student_detail(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, role=CustomUser.Role.STUDENT)
    student_profile = user.student
    enrollments = student_profile.enrollment_set.select_related('class_group')
    return render(request, 'adminportal/student_part/student_detail.html', {
        'user': user,
        'student_profile': student_profile,
        'enrollments': enrollments,
    })

@role_required(CustomUser.Role.ADMIN)
def student_edit(request, pk):
    user = get_object_or_404(CustomUser, pk=pk, role=CustomUser.Role.STUDENT)
    student_profile = user.student
    if request.method == 'POST':
        user_form = StudentUpdateForm(request.POST, instance=user)
        profile_form = StudentProfileUpdateForm(request.POST, request.FILES, instance=student_profile)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Student information updated successfully.")
            return redirect('adminportal:student_detail', pk=pk)
    else:
        user_form = StudentUpdateForm(instance=user)
        profile_form = StudentProfileUpdateForm(instance=student_profile)
    return render(request, 'adminportal/student_edit.html', {
        'user_form': user_form,
        'profile_form': profile_form,
        'user': user,
    })

def enroll_student(request, pk):
    student = get_object_or_404(Student, user_id=pk)
    classgroups = ClassGroup.objects.all()

    if request.method == "POST":
        classgroup_id = request.POST.get("class_group")
        if not classgroup_id:
            messages.error(request, "Please select a class group.")
            return redirect(request.path)
        classgroup = get_object_or_404(ClassGroup, id=classgroup_id)
        if Enrollment.objects.filter(student=student, class_group=classgroup).exists():
            messages.warning(request, f"{student.user.full_name} is already enrolled in {classgroup.name}.")
        else:
            Enrollment.objects.create(student=student, class_group=classgroup)
            messages.success(request, f"{student.user.full_name} enrolled in {classgroup.name} successfully.")
        return redirect('adminportal:student_list')

    return render(request, 'adminportal/student_part/enroll_student.html', {
        'student': student,
        'classgroups': classgroups,
    })

def export_students(request):
    students = CustomUser.objects.filter(role=CustomUser.Role.STUDENT).select_related('department')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=students.csv'
    writer = csv.writer(response)
    writer.writerow(['Name', 'Email', 'Department', 'Date Joined', 'Registration Number', 'Phone Number'])
    for student in students:
        department_name = student.department.name if student.department else '-'
        reg_no = getattr(getattr(student, 'student', None), 'registration_number', '-')
        phone = getattr(student, 'phone_number', '-')
        writer.writerow([
            student.get_full_name(),
            student.email,
            department_name,
            student.date_joined.strftime('%Y-%m-%d'),
            reg_no,
            phone,
        ])
    return response

# ---------- STAFF (Admin) ----------

@role_required(CustomUser.Role.ADMIN)
def staff_list(request):
    staff_users = CustomUser.objects.filter(role=CustomUser.Role.ADMIN).order_by('full_name', 'short_name')
    return render(request, 'adminportal/staff_part/staff_list.html', {'staff_users': staff_users})

@role_required(CustomUser.Role.ADMIN)
def add_staff(request):
    if not request.user.is_superuser:
        messages.error(request, "You are not permitted to add staff. Only superusers can perform this action.", extra_tags='staff')
        return render(request, 'adminportal/staff_part/add_staff.html', {
            'form': None,  # Don't render form!
            'not_permitted': True
        })

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, request.FILES)
        if form.is_valid():
            staff = form.save(commit=False)
            staff.role = CustomUser.Role.ADMIN
            staff.save()
            messages.success(request, "Staff added successfully.", extra_tags='staff')
            return redirect('adminportal:staff_list')
        else:
            messages.error(request, "Please correct the errors in the staff form.", extra_tags='staff')
    else:
        form = CustomUserCreationForm()
    return render(request, 'adminportal/staff_part/add_staff.html', {'form': form, 'not_permitted': False})


# ---------- COURSE MANAGEMENT ----------

@role_required(CustomUser.Role.ADMIN)
def course_list(request):
    courses = Course.objects.all().order_by('name')
    return render(request, 'adminportal/course_part/course_list.html', {'courses': courses})

@role_required(CustomUser.Role.ADMIN)
def add_course(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Course added successfully.")
            return redirect('adminportal:course_list')
    else:
        form = CourseForm()
    return render(request, 'adminportal/course_part/add_course.html', {'form': form})

@role_required(CustomUser.Role.ADMIN)
def edit_course(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect('adminportal:course_list')
    else:
        form = CourseForm(instance=course)
    return render(request, 'adminportal/course_part/edit_course.html', {'form': form, 'course': course})

@role_required(CustomUser.Role.ADMIN)
def assign_lecturer_classgroup(request, pk):
    classgroup = get_object_or_404(ClassGroup, pk=pk)
    if request.method == 'POST':
        form = AssignLecturersToClassGroupForm(request.POST, instance=classgroup)
        if form.is_valid():
            form.save()
            messages.success(request, "Lecturers assigned to class group successfully.")
            return redirect('adminportal:course_list')
    else:
        form = AssignLecturersToClassGroupForm(instance=classgroup)
    return render(request, 'adminportal/course_part/assign_lecturer_course.html', {
        'form': form,
        'classgroup': classgroup,
        'course': classgroup.course,
    })

@role_required(CustomUser.Role.ADMIN)
def export_courses(request):
    import csv
    from django.utils.text import slugify

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="courses_{slugify(str(request.user))}.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'Course Name',
        'Course Code',
        'Subject(s)',
        'Class Group',
        'Academic Year',
        'Classroom',
        'Lecturers (names)',
        'Lecturers (emails)',
        'Number of Students'
    ])

    for course in Course.objects.all():
        # Subjects info (comma-separated)
        subjects = course.subjects.all()
        subjects_str = ', '.join([f"{s.name} ({s.code})" for s in subjects]) if subjects else '-'

        classgroups = course.classgroups.all()
        if classgroups:
            for idx, cg in enumerate(classgroups):
                # Lecturer names and emails
                lecturers = cg.lecturers.all()
                lecturer_names = ', '.join([l.user.full_name for l in lecturers]) if lecturers else '-'
                lecturer_emails = ', '.join([l.user.email for l in lecturers]) if lecturers else '-'
                num_students = cg.students.count() if hasattr(cg, 'students') else '-'

                writer.writerow([
                    course.name if idx == 0 else '',     # Only show course name on first group
                    course.code if idx == 0 else '',     # Only show code on first group
                    subjects_str if idx == 0 else '',
                    cg.name,
                    cg.year,
                    cg.classroom or '-',
                    lecturer_names,
                    lecturer_emails,
                    num_students,
                ])
        else:
            # No class groups
            writer.writerow([
                course.name,
                course.code,
                subjects_str,
                '-',
                '-',
                '-',
                '-',
                '-',
                '-',
            ])
    return response


# ---------- DEPARTMENT MANAGEMENT ----------

@role_required(CustomUser.Role.ADMIN)
def department_list(request):
    departments = Department.objects.all()
    return render(request, 'adminportal/department_part/department_list.html', {'departments': departments})

@role_required(CustomUser.Role.ADMIN)
def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department added successfully.")
            return redirect('adminportal:department_list')
    else:
        form = DepartmentForm()
    return render(request, 'adminportal/department_part/add_department.html', {'form': form})

# ---------- ADD CLASSGROUP & SUBJECT ----------

@role_required(CustomUser.Role.ADMIN)
def add_classgroup(request):
    course_id = request.GET.get("course_id")
    initial = {}
    if course_id:
        try:
            course = Course.objects.get(pk=course_id)
            initial['course'] = course
        except Course.DoesNotExist:
            pass

    if request.method == "POST":
        form = ClassGroupForm(request.POST)
        if form.is_valid():
            classgroup = form.save()
            messages.success(request, f"Class group '{classgroup.name}' added successfully.")
            return redirect('adminportal:edit_course', pk=classgroup.course.pk)
    else:
        form = ClassGroupForm(initial=initial)
    return render(request, 'adminportal/course_part/add_classgroup.html', {'form': form})

@role_required(CustomUser.Role.ADMIN)
def add_subject(request):
    course_id = request.GET.get("course_id")
    initial = {}
    if course_id:
        try:
            course = Course.objects.get(pk=course_id)
            initial['course'] = course
        except Course.DoesNotExist:
            pass

    if request.method == "POST":
        form = SubjectForm(request.POST)
        if form.is_valid():
            subject = form.save()
            messages.success(request, f"Subject '{subject.name}' added successfully.")
            return redirect('adminportal:edit_course', pk=subject.course.pk)
    else:
        form = SubjectForm(initial=initial)
    return render(request, 'adminportal/course_part/add_subject.html', {'form': form})


# ---------- CLASSGROUPS BY DEPARTMENT ----------
@role_required(CustomUser.Role.ADMIN)
def get_classgroups_by_department(request):
    department_id = request.GET.get("department")
    from core.models import ClassGroup
    if department_id:
        classgroups = ClassGroup.objects.filter(department_id=department_id)
    else:
        classgroups = ClassGroup.objects.none()
    # Use the same form, but re-render just the class_group widget
    form = AddStudentForm(initial={"department": department_id})
    form.fields['class_group'].queryset = classgroups
    html = render_to_string('adminportal/student_part/_classgroup_dropdown.html', {'form': form})
    return HttpResponse(html)



@role_required(CustomUser.Role.ADMIN)
def edit_classgroup(request, pk):
    classgroup = get_object_or_404(ClassGroup, pk=pk)
    if request.method == "POST":
        form = ClassGroupForm(request.POST, instance=classgroup)
        if form.is_valid():
            form.save()
            messages.success(request, f"Class group '{classgroup.name}' updated successfully.")
            return redirect('adminportal:edit_course', pk=classgroup.course.pk)
    else:
        form = ClassGroupForm(instance=classgroup)
    return render(request, 'adminportal/course_part/edit_classgroup.html', {
        'form': form,
        'classgroup': classgroup,
        'course': classgroup.course,
    })


# ---------- FEE MANAGEMENT ----------
@role_required(CustomUser.Role.ADMIN)
def fee_plan_list(request):
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    plans = (
        StudentFeePlan.objects
        .select_related("student__user")
        .prefetch_related("installments")
        .all()
    )
    if q:
        plans = plans.filter(
            Q(student__user__full_name__icontains=q) |
            Q(student__user__email__icontains=q) |
            Q(description__icontains=q)
        )
    if status:
        plans = plans.filter(status=status)

    # quick aggregates for the page header
    aggregates = plans.aggregate(
        total=Sum("total_amount"),
        count=Count("id"),
    )

    context = {
        "plans": plans.order_by("-created_at"),
        "q": q,
        "status": status,
        "aggregates": aggregates,
        "statuses": StudentFeePlan.Status.choices,
    }
    return render(request, "adminportal/student_part/fees/fee_plan_list.html", context)

@role_required(CustomUser.Role.ADMIN)
def fee_plan_create(request):
    if request.method == "POST":
        form = FeePlanCreateForm(request.POST)
        if form.is_valid():
            plan = form.save()
            messages.success(request, "Fee plan created. You can now generate installments.")
            return redirect("adminportal:fee_plan_detail", plan_id=plan.id)
    else:
        form = FeePlanCreateForm()
    return render(request, "adminportal/student_part/fees/fee_plan_form.html", {"form": form, "creating_for_student": None})

@role_required(CustomUser.Role.ADMIN)
def fee_plan_create_for_student(request, student_id):
    student = get_object_or_404(Student.objects.select_related("user"), pk=student_id)
    if request.method == "POST":
        form = FeePlanCreateForStudentForm(request.POST)
        if form.is_valid():
            plan = form.save(commit=False)
            plan.student = student
            plan.save()
            messages.success(request, f"Fee plan created for {student.user.get_full_name()}.")
            return redirect("adminportal:fee_plan_detail", plan_id=plan.id)
    else:
        form = FeePlanCreateForStudentForm()
    return render(request, "adminportal/student_part/fees/fee_plan_form.html", {"form": form, "creating_for_student": student})

@role_required(CustomUser.Role.ADMIN)
def fee_plan_detail(request, plan_id):
    plan = get_object_or_404(
        StudentFeePlan.objects.select_related("student__user").prefetch_related("installments"),
        pk=plan_id
    )

    # Inline update of a single installment (optional UX)
    if request.method == "POST":
        inst_id = request.POST.get("installment_id")
        if inst_id:
            inst = get_object_or_404(StudentFeeInstallment, pk=inst_id, plan=plan)
            form = InstallmentUpdateForm(request.POST, instance=inst)
            if form.is_valid():
                obj = form.save(commit=False)
                if obj.is_paid and not obj.paid_date:
                    obj.paid_date = timezone.localdate()
                obj.save()
                messages.success(request, f"Installment #{inst.sequence_no} updated.")
                return redirect("adminportal:fee_plan_detail", plan_id=plan.id)
        messages.error(request, "Invalid form submission.")

    # Derived amounts
    total_due = sum(i.amount for i in plan.installments.all())
    total_paid = sum(i.amount for i in plan.installments.filter(is_paid=True))
    balance = total_due - total_paid

    context = {
        "plan": plan,
        "installments": plan.installments.order_by("sequence_no"),
        "installment_form": InstallmentUpdateForm(),
        "total_due": total_due,
        "total_paid": total_paid,
        "balance": balance,
    }
    return render(request, "adminportal/student_part/fees/fee_plan_detail.html", context)

@role_required(CustomUser.Role.ADMIN)
def fee_plan_generate_installments(request, plan_id):
    plan = get_object_or_404(StudentFeePlan, pk=plan_id)
    created = plan.ensure_installments()
    messages.success(request, f"Installments generated/updated ({created} rows).")
    return redirect("adminportal:fee_plan_detail", plan_id=plan.id)

@role_required(CustomUser.Role.ADMIN)
def installment_toggle_paid(request, pk):
    inst = get_object_or_404(StudentFeeInstallment.objects.select_related("plan"), pk=pk)
    inst.is_paid = not inst.is_paid
    inst.paid_date = timezone.localdate() if inst.is_paid else None
    inst.save(update_fields=["is_paid", "paid_date"])
    messages.success(request, f"Installment #{inst.sequence_no} is now {'PAID' if inst.is_paid else 'UNPAID'}.")
    return redirect("adminportal:fee_plan_detail", plan_id=inst.plan_id)