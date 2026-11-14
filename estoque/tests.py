from decimal import Decimal

from django.test import TestCase

from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.urls import reverse

from .admin import MovimentacaoEstoqueAdmin, ProdutoAdmin
from .forms import MovimentacaoEstoqueForm, ProdutoForm
from .models import Categoria, Fornecedor, MovimentacaoEstoque, Produto


class MovimentacaoEstoqueTests(TestCase):
    def setUp(self):
        self.categoria = Categoria.objects.create(nome='Acessórios')
        self.fornecedor = Fornecedor.objects.create(nome='Fornecedor Exemplo')
        self.produto = Produto.objects.create(
            nome='Teclado',
            sku='TEC-001',
            categoria=self.categoria,
            fornecedor=self.fornecedor,
            preco='100.00',
            quantidade_estoque=5,
        )

    def test_quatro_modelos_e_relacionamentos(self):
        self.assertEqual(Produto.objects.count(), 1)
        self.assertEqual(self.produto.fornecedor, self.fornecedor)

    def test_nao_permite_saida_maior_que_estoque(self):
        movimentacao = MovimentacaoEstoque(
            produto=self.produto,
            tipo=MovimentacaoEstoque.TIPO_SAIDA,
            quantidade=6,
        )

        with self.assertRaises(ValidationError):
            movimentacao.save()

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 5)

    def test_nao_permite_tipo_de_movimentacao_invalido(self):
        movimentacao = MovimentacaoEstoque(
            produto=self.produto,
            tipo='ajuste',
            quantidade=1,
        )

        with self.assertRaises(ValidationError):
            movimentacao.save()

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 5)
        self.assertFalse(MovimentacaoEstoque.objects.exists())

    def test_nao_permite_movimentacao_de_produto_inativo(self):
        self.produto.ativo = False
        self.produto.save()
        movimentacao = MovimentacaoEstoque(
            produto=self.produto,
            tipo=MovimentacaoEstoque.TIPO_ENTRADA,
            quantidade=1,
        )

        with self.assertRaises(ValidationError):
            movimentacao.save()

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 5)

    def test_entrada_atualiza_estoque(self):
        MovimentacaoEstoque.objects.create(
            produto=self.produto,
            tipo=MovimentacaoEstoque.TIPO_ENTRADA,
            quantidade=3,
        )

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 8)

    def test_saida_atualiza_estoque(self):
        MovimentacaoEstoque.objects.create(
            produto=self.produto,
            tipo=MovimentacaoEstoque.TIPO_SAIDA,
            quantidade=3,
        )

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 2)

    def test_movimentacao_registrada_nao_pode_ser_editada(self):
        movimentacao = MovimentacaoEstoque.objects.create(
            produto=self.produto,
            tipo=MovimentacaoEstoque.TIPO_ENTRADA,
            quantidade=3,
        )
        movimentacao.quantidade = 5

        with self.assertRaises(ValidationError):
            movimentacao.save()

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 8)
        self.assertEqual(
            MovimentacaoEstoque.objects.get(pk=movimentacao.pk).quantidade,
            3,
        )

    def test_movimentacao_registrada_nao_pode_ser_excluida(self):
        movimentacao = MovimentacaoEstoque.objects.create(
            produto=self.produto,
            tipo=MovimentacaoEstoque.TIPO_ENTRADA,
            quantidade=3,
        )

        with self.assertRaises(ValidationError):
            movimentacao.delete()

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 8)
        self.assertTrue(MovimentacaoEstoque.objects.filter(pk=movimentacao.pk).exists())

    def test_movimentacao_nao_pode_ser_excluida_em_lote(self):
        movimentacao = MovimentacaoEstoque.objects.create(
            produto=self.produto,
            tipo=MovimentacaoEstoque.TIPO_ENTRADA,
            quantidade=3,
        )

        with self.assertRaises(ValidationError):
            with transaction.atomic():
                MovimentacaoEstoque.objects.filter(pk=movimentacao.pk).delete()

        self.produto.refresh_from_db()
        self.assertEqual(self.produto.quantidade_estoque, 8)
        self.assertTrue(MovimentacaoEstoque.objects.filter(pk=movimentacao.pk).exists())

    def test_preco_nao_positivo_e_bloqueado_pelo_banco(self):
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Produto.objects.filter(pk=self.produto.pk).update(preco='0.00')

    def test_preco_deve_ser_maior_que_zero(self):
        self.produto.preco = '0.00'

        with self.assertRaises(ValidationError):
            self.produto.full_clean()

    def test_saldo_nao_pode_ser_editado_em_produto_existente(self):
        form = ProdutoForm(instance=self.produto)

        self.assertNotIn('quantidade_estoque', form.fields)
        self.assertEqual(ProdutoAdmin.list_editable, ['preco', 'ativo'])
        self.assertIn('quantidade_estoque', ProdutoAdmin.readonly_fields)

    def test_movimentacoes_sao_imutaveis_no_admin(self):
        admin = MovimentacaoEstoqueAdmin(MovimentacaoEstoque, None)

        self.assertFalse(admin.has_change_permission(None))
        self.assertFalse(admin.has_delete_permission(None))

    def test_formularios_exibem_rotulos_com_acentuacao_correta(self):
        produto_form = ProdutoForm()
        movimentacao_form = MovimentacaoEstoqueForm()

        self.assertEqual(produto_form.fields['descricao'].label, 'Descrição')
        self.assertEqual(produto_form.fields['preco'].label, 'Preço')
        self.assertEqual(
            produto_form.fields['quantidade_estoque'].label,
            'Quantidade em estoque',
        )
        self.assertEqual(
            movimentacao_form.fields['tipo'].label,
            'Tipo de movimentação',
        )
        self.assertEqual(movimentacao_form.fields['observacao'].label, 'Observação')
        self.assertEqual(
            list(produto_form.fields['categoria'].choices)[0][1],
            'Selecione uma categoria',
        )
        self.assertEqual(
            list(produto_form.fields['fornecedor'].choices)[0][1],
            'Sem fornecedor',
        )
        self.assertEqual(
            list(movimentacao_form.fields['produto'].choices)[0][1],
            'Selecione um produto',
        )


class CategoriaCrudTests(TestCase):
    def test_categoria_crud_web(self):
        response = self.client.post(
            reverse('categoria_create'),
            {'nome': 'Papelaria', 'descricao': 'Materiais de escritório'},
        )
        self.assertRedirects(response, reverse('categoria_list'))

        categoria = Categoria.objects.get(nome='Papelaria')
        response = self.client.post(
            reverse('categoria_update', args=[categoria.pk]),
            {'nome': 'Escritório', 'descricao': 'Materiais para escritório'},
        )
        self.assertRedirects(response, reverse('categoria_list'))
        self.assertEqual(Categoria.objects.get(pk=categoria.pk).nome, 'Escritório')

        response = self.client.post(reverse('categoria_delete', args=[categoria.pk]))
        self.assertRedirects(response, reverse('categoria_list'))
        self.assertFalse(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_categoria_com_produtos_nao_pode_ser_excluida(self):
        categoria = Categoria.objects.create(nome='Informática')
        Produto.objects.create(
            nome='Mouse',
            sku='MOU-001',
            categoria=categoria,
            preco='50.00',
            quantidade_estoque=2,
        )

        response = self.client.post(reverse('categoria_delete', args=[categoria.pk]))

        self.assertRedirects(response, reverse('categoria_list'))
        self.assertTrue(Categoria.objects.filter(pk=categoria.pk).exists())

    def test_produto_com_movimentacoes_nao_pode_ser_excluido(self):
        categoria = Categoria.objects.create(nome='Informática')
        produto = Produto.objects.create(
            nome='Mouse',
            sku='MOU-002',
            categoria=categoria,
            preco='50.00',
            quantidade_estoque=2,
        )
        MovimentacaoEstoque.objects.create(
            produto=produto,
            tipo=MovimentacaoEstoque.TIPO_ENTRADA,
            quantidade=1,
        )

        response = self.client.post(reverse('produto_delete', args=[produto.pk]), follow=True)

        self.assertContains(response, 'Não é possível excluir um produto que possui movimentações.')
        self.assertTrue(Produto.objects.filter(pk=produto.pk).exists())


class DashboardTests(TestCase):
    def test_dashboard_aplica_regras_para_produtos_inativos(self):
        categoria = Categoria.objects.create(nome='Informática')
        Produto.objects.create(
            nome='Produto ativo com estoque baixo',
            sku='ATV-001',
            categoria=categoria,
            preco='10.00',
            quantidade_estoque=2,
            ativo=True,
        )
        Produto.objects.create(
            nome='Produto ativo com estoque alto',
            sku='ATV-002',
            categoria=categoria,
            preco='2.00',
            quantidade_estoque=9,
            ativo=True,
        )
        Produto.objects.create(
            nome='Produto inativo',
            sku='INA-001',
            categoria=categoria,
            preco='20.00',
            quantidade_estoque=3,
            ativo=False,
        )

        response = self.client.get(reverse('dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['total_produtos'], 2)
        self.assertEqual(response.context['estoque_baixo'], 1)
        self.assertEqual(response.context['valor_total'], Decimal('98.00'))
        self.assertEqual(
            list(response.context['produtos_em_alta'].values_list('sku', flat=True)),
            ['ATV-002', 'ATV-001'],
        )
        self.assertContains(response, 'Produtos ativos')
        self.assertContains(response, 'Valor estimado do estoque (inclui inativos)')
        self.assertNotContains(response, 'theme-toggle')
        self.assertNotContains(response, 'Produto inativo')


class AdminNavigationTests(TestCase):
    def test_admin_login_tem_link_de_volta_para_stock_and_roll(self):
        response = self.client.get(reverse('admin:login'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/">Voltar ao Stock &amp; Roll</a>')

    def test_admin_header_links_back_to_stock_and_roll(self):
        user = get_user_model().objects.create_superuser(
            username='admin-test',
            email='admin@example.com',
            password='test-password',
        )
        self.client.force_login(user)

        response = self.client.get(reverse('admin:index'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'href="/"')
