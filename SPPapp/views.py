import os
import csv
import joblib
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.contrib.auth import authenticate, login, logout as auth_logout
from .models import StockPrediction
from .forms import StockPredictionForm, UserRegistrationForm, UserLoginForm

def get_stock_history(company_name):
    csv_file_path = os.path.join(settings.BASE_DIR, f'{company_name.upper()}.csv')
    dates = []
    prices = []
    volumes = []
    high_prices = []
    low_prices = []
    with open(csv_file_path, 'r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            dates.append(row['Date'])
            prices.append(float(row['Close']))
            volumes.append(float(row['Volume']))
            high_prices.append(float(row['High']))
            low_prices.append(float(row['Low']))
    return dates, prices, volumes, high_prices, low_prices

def get_prediction(form_data, company_name):
    model_path = os.path.join(settings.BASE_DIR, 'models', f'{company_name.lower()}.pkl')
    with open(model_path, 'rb') as model_file:
        model = joblib.load(model_file)

    input_data = [
        form_data['open_price'],
        form_data['high_price'],
        form_data['low_price'],
        form_data['volume']
    ]
    input_data = [input_data]
    predicted_price = model.predict(input_data)[0]
    
    return predicted_price

@login_required
def predict(request, company_name):
    prediction = None
    dates = []
    prices = []
    volumes = []
    high_prices = []
    low_prices = []

    if request.method == 'POST':
        form = StockPredictionForm(request.POST)
        if form.is_valid():
            prediction = form.save(commit=False)
            prediction.user = request.user
            prediction.company = company_name
            prediction.predicted_price = get_prediction(form.cleaned_data, company_name)
            prediction.save()

            dates, prices, volumes, high_prices, low_prices = get_stock_history(company_name)
            return render(request, 'result.html', {
                'company': company_name,
                'prediction': prediction.predicted_price,
                'dates': dates,
                'prices': prices,
                'volumes': volumes,
                'high_prices': high_prices,
                'low_prices': low_prices,
            })
    else:
        form = StockPredictionForm()
        print(company_name)
        
        # Load data for initial view
        dates, prices, volumes, high_prices, low_prices = get_stock_history(company_name)
        print(prices)
    return render(request, f'{company_name.lower()}.html', {
        'form': form,
        'company': company_name,
        'prediction': prediction.predicted_price if prediction else None,
        'dates': dates,
        'prices': prices,
        'volumes': volumes,
        'high_prices': high_prices,
        'low_prices': low_prices,
    })

@login_required
def company_history(request, company_name):
    dates, prices, volumes, high_prices, low_prices = get_stock_history(company_name)
    return JsonResponse({
        'dates': dates,
        'prices': prices,
        'volumes': volumes,
        'high_prices': high_prices,
        'low_prices': low_prices,
    })

def home(request):
    return render(request, 'home.html')

def history(request):
    company_names = ['amazon', 'apple', 'facebook', 'google', 'microsoft']  # List of companies or fetch dynamically

    # Initialize dictionary to hold stock data for all companies
    all_company_data = {
        'companies': []
    }

    for company_name in company_names:
        try:
            dates, prices, volumes, high_prices, low_prices = get_stock_history(company_name)
            all_company_data['companies'].append({
                'name': company_name,
                'dates': dates,
                'prices': prices,
                'volumes': volumes,
                'high_prices': high_prices,
                'low_prices': low_prices
            })
        except FileNotFoundError:
            # Handle case where CSV file for company is not found
            continue

    return render(request, 'history.html', {
        'company_data': all_company_data
    })

@login_required
@login_required
def old_predictions(request):
    old_predictions = StockPrediction.objects.filter(user=request.user)
    company_data = {
        'dates': [],  # Add this line to ensure dates are collected
        'companies': []
    }

    company_names = old_predictions.values_list('company', flat=True).distinct()
    for company_name in company_names:
        dates, prices, volumes, high_prices, low_prices = get_stock_history(company_name)
        company_data['dates'] = dates  # Assuming all companies have the same dates
        company_data['companies'].append({
            'name': company_name,
            'dates': dates,
            'prices': prices
        })

    # Flatten the list of companies to handle chart data more easily
    chart_data = []
    for company in company_data['companies']:
        chart_data.append({
            'name': company['name'],
            'dates': company['dates'],
            'prices': company['prices']
        })
    print(dates)

    return render(request, 'old_predictions.html', {
        'old_predictions': old_predictions,
        'chart_data': chart_data,
        'dates': company_data['dates']  # Ensure dates are passed to the template
    })


def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            login(request, user)
            return redirect(home)
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = UserLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect(home)
            else:
                form.add_error(None, 'Invalid username or password')
    else:
        form = UserLoginForm()
    return render(request, 'login.html', {'form': form})

def logout_view(request):
    auth_logout(request)
    return redirect('home')

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})