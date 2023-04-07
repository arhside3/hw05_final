from django.core.paginator import Paginator

from yatube.settings import PAGE_SIZE


def paginate(request, posts, pagesize=PAGE_SIZE):
    paginator = Paginator(posts, pagesize)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
