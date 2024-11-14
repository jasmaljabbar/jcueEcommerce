from admin_sid.models import Category

def categories(request):
    cat = Category.objects.all()
    return {'cat': cat}