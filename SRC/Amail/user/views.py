from django.utils.encoding import force_str
from .token import account_activation_token
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.contrib import messages
from django.shortcuts import render, redirect
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.views.generic import FormView, View
from .forms import *
from .models import *
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse


class SignUpView(FormView):
    form_class = SignUpForm
    template_name = 'user/sign_up.html'
    success_url = 'login'

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = False
        user.username += "@Amail.com"
        user.save()
        current_site = get_current_site(self.request)
        subject = 'Activate Your MySite Account'
        message = render_to_string('user/account_activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        user.email_user(subject, message)

        messages.success(self.request, 'Please Confirm your email to complete registration.')

        return redirect('login')


class ActivateAccount(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            user.save()
            login(request, user)
            messages.success(request, 'Your account have been confirmed.')
            return redirect('login')

        messages.warning(request, 'The confirmation link was invalid, possibly because it has already been used.')
        return redirect('signup')


class LogInView(FormView):
    form_class = LogInForm
    template_name = 'user/login.html'
    success_url = 'home'

    def get(self, *args, **kwargs):
        if self.request.user.is_authenticated:
            return redirect('home')
        return self.render_to_response(self.get_context_data())

    def form_valid(self, form):
        user = authenticate(self.request, **form.cleaned_data)
        if user is not None:
            login(self.request, user)
            messages.info(self.request, f"You are now logged in as {form.username}")
            return redirect('home')

        messages.error(self.request, "Invalid username or password.")
        return redirect('home')


@login_required(login_url="login")
def logout_user(request):
    logout(request)
    return redirect(reverse('login'))


class ActivateAccountForgotPassword(View):
    def get(self, request, uidb64, token, *args, **kwargs):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and account_activation_token.check_token(user, token):
            user.is_active = True
            login(request, user)
            messages.success(request, 'Your account have been confirmed.')
            return redirect('change_password')

        messages.warning(request, 'The confirmation link was invalid, possibly because it has already been used.')
        return redirect('signup')


class ForgotPassword(FormView):
    form_class = ForgetPasswordForm
    template_name = 'user/forgot_password.html'
    success_url = 'change_password'

    def form_valid(self, form):
        user: User = form.cleaned_data.get('email')
        user.is_active = False
        user.save()
        current_site = get_current_site(self.request)
        subject = 'Activate Your MySite Account'
        message = render_to_string('user/forgot_activation_email.html', {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': account_activation_token.make_token(user),
        })
        user.email_user(subject, message)
        messages.success(self.request, 'Please Confirm your email to change password.')
        return redirect(reverse('change_password'))


class ChangePassword(FormView):
    form_class = ChangePasswordForm
    template_name = 'user/change_password.html'
    success_url = 'home'

    # def form_valid(self, form):
    #     email = form.cleaned_data['email']
    #     u = User.objects.get(username='john')
    #     u.set_password('new password')
    #     u.save()


@login_required(login_url='login')
def home(request):
    return render(request, 'user/home.html')
