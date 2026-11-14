from django.contrib import admin
from .models import Categoria, Fornecedor, MovimentacaoEstoque, Produto


@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ['nome', 'descricao']
    search_fields = ['nome']


@admin.register(Fornecedor)
class FornecedorAdmin(admin.ModelAdmin):
    list_display = ['nome', 'email', 'telefone', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome', 'email']


@admin.register(Produto)
class ProdutoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'sku', 'categoria', 'fornecedor', 'preco', 'quantidade_estoque', 'ativo']
    list_filter = ['categoria', 'fornecedor', 'ativo']
    search_fields = ['nome', 'sku', 'fornecedor__nome']
    list_editable = ['preco', 'ativo']
    readonly_fields = ['quantidade_estoque']


@admin.register(MovimentacaoEstoque)
class MovimentacaoEstoqueAdmin(admin.ModelAdmin):
    list_display = ['produto', 'tipo', 'quantidade', 'data']
    list_filter = ['tipo', 'data']
    search_fields = ['produto__nome', 'observacao']

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.site_header = 'Stock & Roll | Administração'
admin.site.site_title = 'Stock & Roll'
admin.site.index_title = 'Gestão do estoque'
admin.site.site_url = '/'
