from django import forms
from .models import Categoria, Fornecedor, MovimentacaoEstoque, Produto


class CategoriaForm(forms.ModelForm):
    class Meta:
        model = Categoria
        fields = ['nome', 'descricao']
        labels = {
            'nome': 'Nome',
            'descricao': 'Descrição',
        }


class FornecedorForm(forms.ModelForm):
    class Meta:
        model = Fornecedor
        fields = ['nome', 'email', 'telefone', 'ativo']
        labels = {
            'nome': 'Nome',
            'email': 'E-mail',
            'telefone': 'Telefone',
            'ativo': 'Ativo',
        }


class ProdutoForm(forms.ModelForm):
    class Meta:
        model = Produto
        fields = [
            'nome',
            'sku',
            'categoria',
            'fornecedor',
            'descricao',
            'preco',
            'quantidade_estoque',
            'ativo',
        ]
        labels = {
            'nome': 'Nome do produto',
            'sku': 'SKU',
            'categoria': 'Categoria',
            'fornecedor': 'Fornecedor',
            'descricao': 'Descrição',
            'preco': 'Preço',
            'quantidade_estoque': 'Quantidade em estoque',
            'ativo': 'Ativo',
        }
        widgets = {
            'descricao': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categoria'].empty_label = 'Selecione uma categoria'
        self.fields['fornecedor'].empty_label = 'Sem fornecedor'
        if self.instance.pk:
            self.fields.pop('quantidade_estoque')

    def clean_preco(self):
        preco = self.cleaned_data.get('preco')
        if preco is not None and preco <= 0:
            raise forms.ValidationError('O preço deve ser maior que zero.')
        return preco

    def clean_quantidade_estoque(self):
        quantidade = self.cleaned_data.get('quantidade_estoque')
        if quantidade is not None and quantidade < 0:
            raise forms.ValidationError('A quantidade em estoque não pode ser negativa.')
        return quantidade


class MovimentacaoEstoqueForm(forms.ModelForm):
    class Meta:
        model = MovimentacaoEstoque
        fields = ['produto', 'tipo', 'quantidade', 'observacao']
        labels = {
            'produto': 'Produto',
            'tipo': 'Tipo de movimentação',
            'quantidade': 'Quantidade',
            'observacao': 'Observação',
        }
        widgets = {
            'observacao': forms.TextInput(attrs={'placeholder': 'Descreva o motivo da movimentação'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['produto'].empty_label = 'Selecione um produto'

    def clean(self):
        cleaned_data = super().clean()
        produto = cleaned_data.get('produto')
        tipo = cleaned_data.get('tipo')
        quantidade = cleaned_data.get('quantidade')

        if produto and tipo and quantidade:
            if tipo == MovimentacaoEstoque.TIPO_SAIDA and quantidade > produto.quantidade_estoque:
                raise forms.ValidationError('Não há quantidade suficiente em estoque para essa saída.')

        return cleaned_data
