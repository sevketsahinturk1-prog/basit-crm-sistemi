"""İş mantığı: müşteri, satış, destek modelleri."""

from crm.models.destek_talebi import DestekTalebi
from crm.models.musteri import Musteri
from crm.models.satis import Satis

__all__ = ["Musteri", "Satis", "DestekTalebi"]
