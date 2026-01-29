from .models import UserBook
from django.db import IntegrityError
from .models import Book, Shelf, UserBook
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .models import Shelf
import requests
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404



@login_required
def book_list(request):
    q = request.GET.get("q", "")
    user_books = UserBook.objects.filter(user=request.user)

    if q:
        user_books = user_books.filter(book__title__icontains=q)

    return render(
        request,
        "sinnsa/book_list.html",
        {
            "user_books": user_books,
            "q": q,
        },
    )


@login_required
def book_add(request):
    # 棚の選択肢（ログイン前提にするなら user=request.user にしてOK）
    shelves = Shelf.objects.filter(user=request.user)

    error = ""
    if request.method == "POST":
        isbn = (request.POST.get("isbn") or "").strip()
        title = (request.POST.get("title") or "").strip()
        author = (request.POST.get("author") or "").strip()
        publisher = (request.POST.get("publisher") or "").strip()
        cover_url = (request.POST.get("cover_url") or "").strip()
        memo = (request.POST.get("memo") or "").strip()
        shelf_id = request.POST.get("shelf") or ""

        # 超最低限のバリデーション
        if not isbn:
            error = "ISBNを入力してください"
        elif not title:
            error = "タイトルを入力してください"
        else:
            # 棚（任意）
            shelf = None
            if shelf_id:
                shelf = Shelf.objects.filter(id=shelf_id).first()

            # BookはISBNで一意：なければ作る、あれば更新（空欄は潰さないように）
            book, created = Book.objects.get_or_create(
                isbn=isbn,
                defaults={
                    "title": title,
                    "author": author,
                    "publisher": publisher,
                    "cover_url": cover_url,
                },
            )
            if not created:
                # 既存のBookがあって、フォームで入ってきた情報があれば更新
                updated = False
                if title and book.title != title:
                    book.title = title
                    updated = True
                if author and book.author != author:
                    book.author = author
                    updated = True
                if publisher and book.publisher != publisher:
                    book.publisher = publisher
                    updated = True
                if cover_url and book.cover_url != cover_url:
                    book.cover_url = cover_url
                    updated = True
                if updated:
                    book.save()

            # UserBook作成（ダブりはunique_togetherで弾かれる）
            try:
                UserBook.objects.create(
                    user=request.user,  # ※ログインしてないとAnonymousUserでエラーになる
                    book=book,
                    shelf=shelf,
                    memo=memo,
                )
                return redirect("book_list")
            except IntegrityError:
                error = "その本はすでに登録されています（ダブり防止）"

    return render(
        request,
        "sinnsa/book_add.html",
        {
            "shelves": shelves,
            "error": error,
        },
    )


def signup(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()  # ユーザー作成
            login(request, user)  # 作成後そのままログイン
            return redirect("book_list")
    else:
        form = UserCreationForm()

    return render(request, "signup.html", {"form": form})


@login_required
def shelf_list_create(request):
    error = ""

    if request.method == "POST":
        name = (request.POST.get("name") or "").strip()
        if not name:
            error = "棚の名前を入力してください"
        else:
            try:
                Shelf.objects.create(user=request.user, name=name)
                return redirect("shelf_list_create")
            except IntegrityError:
                error = "同じ名前の棚はすでにあります"

    shelves = Shelf.objects.filter(user=request.user)
    return render(
        request,
        "sinnsa/shelves.html",
        {
            "shelves": shelves,
            "error": error,
        },
    )


@login_required
def isbn_lookup(request):
    isbn = (request.GET.get("isbn") or "").strip().replace("-", "")
    if not isbn:
        return JsonResponse({"ok": False, "error": "ISBNが空です"})

    url = f"https://api.openbd.jp/v1/get?isbn={isbn}"
    r = requests.get(url, timeout=10)
    data = r.json()

    # OpenBDは配列で返る。見つからないと [None]
    if not data or data[0] is None:
        return JsonResponse({"ok": False, "error": "見つかりませんでした"})

    item = data[0]

    # タイトルなどの取り出し（無い場合もあるので安全に）
    title = (
        item.get("summary", {}).get("title")
        or item.get("onix", {})
        .get("DescriptiveDetail", {})
        .get("TitleDetail", {})
        .get("TitleElement", {})
        .get("TitleText", {})
        .get("content")
        or ""
    )
    author = item.get("summary", {}).get("author", "") or ""
    publisher = item.get("summary", {}).get("publisher", "") or ""

    cover_url = ""
    # summary.cover が入ることが多い
    cover_url = item.get("summary", {}).get("cover", "") or ""
    # ダメなら onix 側から拾う
    if not cover_url:
        resources = (
            item.get("onix", {})
            .get("CollateralDetail", {})
            .get("SupportingResource", [])
        )
        if resources:
            rv = resources[0].get("ResourceVersion", [])
            if rv:
                cover_url = rv[0].get("ResourceLink", "") or ""

    return JsonResponse(
        {
            "ok": True,
            "isbn": isbn,
            "title": title,
            "author": author,
            "publisher": publisher,
            "cover_url": cover_url,
        }
    )


@login_required
def userbook_edit(request, pk):
    ub = get_object_or_404(UserBook, pk=pk, user=request.user)
    shelves = Shelf.objects.filter(user=request.user).order_by("name")
    error = ""

    if request.method == "POST":
        shelf_id = request.POST.get("shelf") or ""
        memo = (request.POST.get("memo") or "").strip()

        # 棚は任意
        shelf = None
        if shelf_id:
            shelf = Shelf.objects.filter(id=shelf_id, user=request.user).first()
            if shelf is None:
                error = "その棚は選べません"
        if not error:
            ub.shelf = shelf
            ub.memo = memo
            ub.save()
            return redirect("book_list")

    return render(
        request,
        "sinnsa/userbook_edit.html",
        {
            "ub": ub,
            "shelves": shelves,
            "error": error,
        },
    )


@login_required
def userbook_delete(request, pk):
    ub = get_object_or_404(UserBook, pk=pk, user=request.user)

    if request.method == "POST":
        ub.delete()
        return redirect("book_list")

    return render(request, "sinnsa/userbook_confirm_delete.html", {"ub": ub})
