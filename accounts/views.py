from django.shortcuts import render,redirect
from django.http import HttpResponse
from .forms import  UserForm
from vendor.forms import VendorForm
from .models import User,UserProfile
from django.contrib import messages,auth
from .utils import detectUser,send_verfication_email,send_password_reset_email
from django.contrib.auth.decorators import login_required,user_passes_test
from django.core.exceptions import PermissionDenied
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from vendor.models import Vendor


# Restiction of vedor from accessing the customer page
def check_role_vendor(user):
    if user.role == 1:
        return True
    else:
        raise PermissionDenied

# Restiction of customer from accessing the vendor page
def check_role_customer(user):
    if user.role == 2:
        return True
    else:
        raise PermissionDenied





def registerUser(request):
    if request.user.is_authenticated:
        messages.warning(request,'You already login')
        return redirect('dashboard')
    elif request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            user = form.save(commit=False)
            user.set_password(password)
            user.role = User.CUSTOMER
            user.save()
            
            # Sending Verfication Email
            send_verfication_email(request,user)


            messages.success(request,'Your Account Has Been Registerd Sucessfully!')
            return redirect('registerUser')
        else:
            print(form.errors)
    else:
        form = UserForm()
    context = {
        'form':form,
    }


    return render(request, 'accounts/registerUser.html',context)

def registerVender(request):
    if request.user.is_authenticated:
        messages.warning(request,'You already registered plus logged in into your account ')
        return redirect('vendorDashboard')
    
    elif request.method == 'POST':
        form = UserForm(request.POST)
        v_form = VendorForm(request.POST,request.FILES)
        if form.is_valid() and v_form.is_valid:
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            username = form.cleaned_data['username']
            email = form.cleaned_data['email']
            password = form.cleaned_data['password']
            user = User.objects.create_user(first_name=first_name,last_name=last_name,username=username,email=email,password=password)
            user.role = User.VENDOR
            user.save()
            vendor =  v_form.save(commit=False)
            vendor.user = user
            user_profile = UserProfile.objects.get(user=user)
            vendor.user_profile = user_profile
            vendor.save()

            # Sending Verfication Email
            send_verfication_email(request,user)
            
            messages.success(request,"We're Happy To Join With Us!. Please Wait For The Approval")
            return redirect('registerVendor')
        else:
            print(form.errors)
               
    else:
        form = UserForm()
        v_form = VendorForm()
        
    

    context = {
        'form':form,
        'v_form':v_form,
    }


    return render(request,'accounts/registerVender.html',context)


def activate(request,uidb64,token):
    # activating the user by setting is__active= True when he click that link
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        messages.success(request,'Congratulations! your account is active now')
        return redirect('myAccount')
    else:

        messages.error(request,'Sorry! we get some trouble to activate your account')
        return redirect('myAccount')


def login(request):
    if request.user.is_authenticated:
        messages.warning(request,'You already login')
        return redirect('myAccount')
    elif request.method == 'POST':
        email = request.POST['email']
        password = request.POST['password']

        user = auth.authenticate(email=email,password=password)

        if user is not None:
            auth.login(request,user)
            messages.success(request,'You are now logged in.')
            return redirect('myAccount')
        else:
            messages.error(request,'Invalid login credentials ')
            return redirect('login')
    return render(request,'accounts/login.html')

def logout(request):
    auth.logout(request)
    messages.info(request,'You logged out of your account')
    return redirect('login')

@login_required(login_url = 'login')
def myAccount(request):
    user = request.user
    redirectUrl = detectUser(user)
    return redirect(redirectUrl)

@login_required(login_url = 'login')  
@user_passes_test(check_role_customer)
def custDashboard(request):
    return render(request,'accounts/custDashbaord.html')

@login_required(login_url = 'login')
@user_passes_test(check_role_vendor)
def vendorDashboard(request):
    vendor = Vendor.objects.get(user=request.user)
    context = {
        'vendor': vendor
    }

    return render(request,'accounts/vendorDashbaord.html',context)


def forgot_password(request):
    if request.method == 'POST':
        email = request.POST['email']

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email__exact=email)


            #
            send_password_reset_email(request,user)
            messages.success(request,'We have sent you out that message please to your inbox and check it!')
            return redirect('login')
        else:
            messages.error(request,"We couldn't find your email")
            return redirect(request,'forgot_password')




    return render(request,'accounts/forgot_password.html')


def reset_password_validate(request,uidb64,token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User._default_manager.get(pk=uid)
    except(TypeError,ValueError,OverflowError,User.DoesNotExist):
        user = None
    if user is not None and default_token_generator.check_token(user, token):
        request.session['uid'] = uid
        messages.info(request,'Please reset your password')
        return redirect('reset_password')
    else:
        messages.error(request,'Your Link Expired')
        return redirect('myAccount')

def reset_password(request):
    if request.method == 'POST':
        password = request.POST['password']
        confirm_password = request.POST['confirm_password']

        if password == confirm_password:
            pk = request.session.get('uid')
            user = User.objects.get(pk=pk)
            user.set_password(password)
            user.is_active = True
            user.save()
            messages.success(request,'You reset your password!')
            return redirect('login')
        else:
            messages.error(request,'Password do not match!')
            return redirect('reset_password')
 

    return render(request,'accounts/reset_password.html')