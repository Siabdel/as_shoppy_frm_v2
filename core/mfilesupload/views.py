from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from .forms import ImagesForm
from .models import Image

# Create your views here.
def index(request):
    images = Image.objects.all()
    context = {'images': images}
    return render(request, "image_list.html", context)
def fileupload(request):
    form = ImagesForm(request.POST, request.FILES)
    if request.method == 'POST':
        images = request.FILES.getlist('pic')
        for image in images:
            image_ins = Image(pic = image)
            image_ins.save()
        return redirect('index')
    context = {'form': form}
    return render(request, "upload.html", context)