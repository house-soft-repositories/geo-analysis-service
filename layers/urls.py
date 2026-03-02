from django.urls import path
from .views import ListarCamadasView, ImportarCamadaView, RemoverCamadaView

urlpatterns = [
    path("", ListarCamadasView.as_view(), name="listar-camadas"),
    path("import/", ImportarCamadaView.as_view(), name="importar-camada"),
    path("<str:tipo>/<int:pk>/", RemoverCamadaView.as_view(), name="remover-camada"),
]
