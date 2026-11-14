from django.core.exceptions import ValidationError
from django.db import models, transaction
from django.db.models.signals import pre_delete
from django.dispatch import receiver


class Categoria(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Categoria'
        verbose_name_plural = 'Categorias'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Fornecedor(models.Model):
    nome = models.CharField(max_length=150)
    email = models.EmailField(blank=True)
    telefone = models.CharField(max_length=20, blank=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Produto(models.Model):
    nome = models.CharField(max_length=150)
    sku = models.CharField(max_length=40, unique=True)
    categoria = models.ForeignKey('Categoria', on_delete=models.PROTECT, related_name='produtos')
    fornecedor = models.ForeignKey(
        'Fornecedor',
        on_delete=models.SET_NULL,
        related_name='produtos',
        null=True,
        blank=True,
    )
    descricao = models.TextField(blank=True)
    preco = models.DecimalField(max_digits=10, decimal_places=2)
    quantidade_estoque = models.PositiveIntegerField(default=0)
    ativo = models.BooleanField(default=True)
    data_cadastro = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']
        constraints = [
            models.CheckConstraint(
                condition=models.Q(preco__gt=0),
                name='produto_preco_positivo',
            ),
        ]

    def __str__(self):
        return f'{self.nome} ({self.sku})'

    def clean(self):
        super().clean()
        if self.preco is not None and self.preco <= 0:
            raise ValidationError({'preco': 'O preço deve ser maior que zero.'})
        if self.quantidade_estoque < 0:
            raise ValidationError({'quantidade_estoque': 'A quantidade em estoque não pode ser negativa.'})


class MovimentacaoEstoque(models.Model):
    TIPO_ENTRADA = 'entrada'
    TIPO_SAIDA = 'saida'
    TIPOS = [
        (TIPO_ENTRADA, 'Entrada'),
        (TIPO_SAIDA, 'Saída'),
    ]

    produto = models.ForeignKey('Produto', on_delete=models.PROTECT, related_name='movimentacoes')
    tipo = models.CharField(max_length=10, choices=TIPOS)
    quantidade = models.PositiveIntegerField()
    observacao = models.CharField(max_length=255, blank=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f'{self.produto.nome} - {self.get_tipo_display()} ({self.quantidade})'

    def clean(self):
        super().clean()
        if self.quantidade <= 0:
            raise ValidationError({'quantidade': 'A quantidade deve ser maior que zero.'})
        if self.tipo not in dict(self.TIPOS):
            raise ValidationError({'tipo': 'Selecione um tipo de movimentação válido.'})
        if self.produto_id and not self.produto.ativo:
            raise ValidationError({'produto': 'Não é permitido movimentar um produto inativo.'})
        if self.tipo == self.TIPO_SAIDA and self.quantidade > self.produto.quantidade_estoque:
            raise ValidationError({'quantidade': 'Não há quantidade suficiente em estoque para essa saída.'})

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValidationError('Movimentações registradas não podem ser editadas.')

        with transaction.atomic():
            self.produto = Produto.objects.select_for_update().get(pk=self.produto_id)
            self.clean()
            super().save(*args, **kwargs)

            if self.tipo == self.TIPO_ENTRADA:
                self.produto.quantidade_estoque += self.quantidade
            else:
                self.produto.quantidade_estoque -= self.quantidade
            self.produto.save(update_fields=['quantidade_estoque'])

    def delete(self, *args, **kwargs):
        raise ValidationError('Movimentações registradas não podem ser excluídas.')


@receiver(pre_delete, sender=MovimentacaoEstoque)
def impedir_exclusao_em_lote_de_movimentacao(sender, instance, **kwargs):
    raise ValidationError('Movimentações registradas não podem ser excluídas.')
