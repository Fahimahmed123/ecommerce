from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib import messages

from .models.product import Product
from .models.category import Category
from .models.customer import Customer
from .models.cart import Cart
from .models.order import OrderDetail

from django.db.models import Q
from django.http import JsonResponse

def home(request):
    product = None
    totalitem = 0
    if request.session.has_key('phone'):
        phone = request.session['phone']
        category = Category.get_all_categories()

        customer = Customer.objects.filter(phone=phone)
        totalitem = len(Cart.objects.filter(phone=phone))

        for c in customer:
            name = c.name
            # filtering by category
            categoryID = request.GET.get('category')
            if categoryID:
                product = Product.get_all_product_by_category_id(categoryID)
            else:
                product = Product.get_all_products()

            data = {}
            data['name']= name
            data['product'] = product
            data['category'] = category
            data['totalitem'] = totalitem

            return render(request, "home.html", data)


    else:
        return redirect('login')



def signup(request):
    if request.method == 'GET':
        return render(request, "signup.html")
    else:
        postData = request.POST
        name = postData.get('name')
        phone = postData.get('phone')

        error_messege = None
        value ={
            'name':name,
            'phone':phone
        }

        customer = Customer(name=name, phone=phone)

        # va;idation part
        if (not name):
            error_messege = "Name is required"
        elif not phone:
            error_messege = "Phone Number is required"
        elif len(phone) < 11:
            error_messege = "Phone Number must be larger than 11"
        elif customer.isExist():
            error_messege = "Phone Number already exists"

        if not error_messege:
            messages.success(request, 'Congratulations !!! Registration Successful')
            customer.register()
            return redirect("signup")

        else:
            data ={
                'error':error_messege,
                'value':value
            }
            return render(request, "signup.html", data)

def login(request):
    if request.method == 'GET':
        return render(request,"login.html")
    else:
        phone = request.POST.get('phone')
        value ={
            'phone':phone
        }
        error_message = None
        customer = Customer.objects.filter(phone=request.POST['phone'])
        if customer:
            # session part
            request.session['phone'] = phone
            return redirect("homepage")
        else:
            error_message= "Phone number is Invalid !!!"
            data={
                'value':value,
                'error':error_message
            }

        return render(request, "login.html",data)

def productdetails(request, pk):

    product = Product.objects.get(pk=pk)
    item_already_in_cart = False
    totalitem = 0
    if request.session.has_key('phone'):
        phone = request.session['phone']
        totalitem = len(Cart.objects.filter(phone=phone))
        item_already_in_cart = Cart.objects.filter(Q(product=product.id) & Q(phone=phone)).exists()
        customer = Customer.objects.filter(phone=phone)
        for c in customer:
            name = c.name
        data ={
            'product': product,
            'item_already_in_cart':item_already_in_cart,
            'name':name,
            'totalitem':totalitem

        }
        return render(request, "productdetail.html",data)

def logout(request):
    if request.session.has_key('phone'):
        del request.session['phone']
        return redirect('login')
    else:
        return redirect('login')

def add_to_cart(request):
    phone = request.session['phone']
    product_id = request.GET.get('prod_id')
    product_name = Product.objects.get(id=product_id)
    product = Product.objects.filter(id=product_id)

    for p in product:
        image = p.image
        price = p.price
        Cart(phone=phone,product=product_name,image=image,price=price).save()
        return redirect(f'/product-detail/{product_id}')

def show_cart(request):
    totalitem = 0
    if request.session.has_key('phone'):
        phone = request.session['phone']
        totalitem = len(Cart.objects.filter(phone=phone))

        customer = Customer.objects.filter(phone=phone)
        for c in customer:
            name = c.name
            cart = Cart.objects.filter(phone=phone)
            if cart:
                data={
                    'name':name,
                    'totalitem':totalitem,
                    'cart':cart
                }
                return render(request,"show_cart.html",data)
            else:
                data = {
                    'name': name,
                    'totalitem': totalitem,
                    'cart': cart
                }
                return render(request,"empty_cart.html", data)

def plus_cart(request):
    if request.session.has_key('phone'):
        phone = request.session['phone']
        product_id = request.GET.get("prod_id")

        # Fetch the first matching cart item
        cart = Cart.objects.filter(Q(product=product_id) & Q(phone=phone)).first()

        if cart:
            cart.quantity += 1
            cart.save()
            return JsonResponse({'quantity': cart.quantity})
        else:
            return JsonResponse({'error': 'Cart item not found'}, status=404)

    return JsonResponse({'error': 'User not logged in'}, status=403)


def minus_cart(request):
    if request.session.has_key('phone'):
        phone = request.session['phone']
        product_id = request.GET.get("prod_id")

        # Fetch the first matching cart item
        cart = Cart.objects.filter(Q(product=product_id) & Q(phone=phone)).first()

        if cart:
            cart.quantity -= 1
            cart.save()
            return JsonResponse({'quantity': cart.quantity})
        else:
            return JsonResponse({'error': 'Cart item not found'}, status=404)

    return JsonResponse({'error': 'User not logged in'}, status=403)


def remove_cart(request):
    if request.session.has_key('phone'):
        phone = request.session['phone']
        product_id = request.GET.get("prod_id")

        # Fetch the first matching cart item
        cart = Cart.objects.filter(Q(product=product_id) & Q(phone=phone)).first()

        if cart:

            cart.delete()
            # return render(request,'show_cart.html')
            return JsonResponse("Delete Successful!")


def checkout(request):
    totalitem = 0
    if request.session.has_key('phone'):
        phone = request.session['phone']
        name = request.POST.get('name')
        address = request.POST.get('address')
        mobile = request.POST.get('mobile')

        cart_product = Cart.objects.filter(phone=phone)

        for c in cart_product:
            qty = c.quantity
            price = c.price
            product_name = c.product
            image = c.image
            OrderDetail(user=phone, product_name=product_name, image=image, qty=qty, price=price).save()
            cart_product.delete()
            totalitem = len(Cart.objects.filter(phone=phone))

            customer = Customer.objects.filter(phone=phone)
            for c in customer:
                name = c.name
            data ={
                'name':name,
                'totalitem':totalitem
            }

            return render(request,"empty_cart.html",data)
    else:
        return redirect('login')

def order(request):

    totalitem = 0
    if request.session.has_key('phone'):
        phone = request.session['phone']

        totalitem = len(Cart.objects.filter(phone=phone))

        customer = Customer.objects.filter(phone=phone)
        for c in customer:
            name = c.name
            order = OrderDetail.objects.filter(user=phone)
            data = {
                'order': order,
                'name': name,
                'totalitem': totalitem
            }

            if order:
                return render(request, "order.html", data)

            else:
                return render(request,"emptyorder.html",data)

        else:
            return redirect("login")

def search(request):
    totalitem = 0
    if request.session.has_key('phone'):
        phone = request.session['phone']
        query = request.GET.get('query')
        search = Product.objects.filter(name__contains=query)
        category = Category.get_all_categories()

        totalitem = len(Cart.objects.filter(phone=phone))

        customer = Customer.objects.filter(phone=phone)
        for c in customer:
            name = c.name
            data = {

                'name': name,
                'totalitem': totalitem,
                'search':search,
                'category':category,
                'query':query
            }

            return render(request, 'search.html',data)
    else:
        return redirect('login')