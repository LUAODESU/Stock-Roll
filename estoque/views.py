from decimal import Decimal

from django.contrib import messages
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import CategoriaForm, MovimentacaoEstoqueForm, ProdutoForm
from .models import Categoria, Produto


def dashboard(request):
    produtos_ativos = Produto.objects.filter(ativo=True)
    total_produtos = produtos_ativos.count()
    total_categorias = Categoria.objects.count()
    estoque_baixo = produtos_ativos.filter(quantidade_estoque__lte=5).count()
    valor_total = sum(
        (produto.preco * Decimal(produto.quantidade_estoque) for produto in Produto.objects.all()),
        Decimal('0.00'),
    )
    produtos_em_alta = produtos_ativos.select_related('categoria').order_by('-quantidade_estoque')[:5]

    context = {
        'total_produtos': total_produtos,
        'total_categorias': total_categorias,
        'estoque_baixo': estoque_baixo,
        'valor_total': valor_total,
        'produtos_em_alta': produtos_em_alta,
    }
    return render(request, 'estoque/index.html', context)


def categoria_list(request):
    categorias = Categoria.objects.annotate(total_produtos=Count('produtos'))
    return render(request, 'estoque/categoria_list.html', {'categorias': categorias})


def categoria_create(request):
    form = CategoriaForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoria cadastrada com sucesso!')
        return redirect('categoria_list')
    return render(request, 'estoque/categoria_form.html', {'form': form, 'titulo': 'Cadastrar categoria'})


def categoria_update(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    form = CategoriaForm(request.POST or None, instance=categoria)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Categoria atualizada com sucesso!')
        return redirect('categoria_list')
    return render(request, 'estoque/categoria_form.html', {'form': form, 'titulo': 'Editar categoria'})


def categoria_delete(request, pk):
    categoria = get_object_or_404(Categoria, pk=pk)
    if request.method == 'POST':
        try:
            categoria.delete()
        except ProtectedError:
            messages.error(request, 'Não é possível excluir uma categoria que possui produtos.')
        else:
            messages.success(request, 'Categoria removida com sucesso!')
        return redirect('categoria_list')
    return render(request, 'estoque/categoria_delete.html', {'categoria': categoria})


def produto_list(request):
    query = request.GET.get('q')
    produtos = Produto.objects.select_related('categoria')
    if query:
        produtos = produtos.filter(nome__icontains=query) | produtos.filter(sku__icontains=query)
    context = {'produtos': produtos.order_by('nome'), 'query': query or ''}
    return render(request, 'estoque/produto_list.html', context)


def produto_detail(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    movimentacoes = produto.movimentacoes.order_by('-data')[:10]
    context = {'produto': produto, 'movimentacoes': movimentacoes}
    return render(request, 'estoque/produto_detail.html', context)


def produto_create(request):
    form = ProdutoForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Produto cadastrado com sucesso!')
        return redirect('produto_list')
    return render(request, 'estoque/produto_form.html', {'form': form, 'titulo': 'Cadastrar produto'})


def produto_update(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    form = ProdutoForm(request.POST or None, instance=produto)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Produto atualizado com sucesso!')
        return redirect('produto_list')
    return render(request, 'estoque/produto_form.html', {'form': form, 'titulo': 'Editar produto', 'objeto': produto})


def produto_delete(request, pk):
    produto = get_object_or_404(Produto, pk=pk)
    if request.method == 'POST':
        try:
            produto.delete()
        except ProtectedError:
            messages.error(request, 'Não é possível excluir um produto que possui movimentações.')
        else:
            messages.success(request, 'Produto removido com sucesso!')
        return redirect('produto_list')
    return render(request, 'estoque/produto_delete.html', {'produto': produto})


def movimentacao_create(request):
    form = MovimentacaoEstoqueForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, 'Movimentação registrada com sucesso!')
        return redirect('produto_list')
    return render(request, 'estoque/movimentacao_form.html', {'form': form, 'titulo': 'Registrar movimentação'})
