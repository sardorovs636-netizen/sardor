import tempfile
import unittest
from pathlib import Path

from src import FactorySystem


class FactorySystemTest(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_file = Path(self.temp_dir.name) / "test.db"
        self.system = FactorySystem(str(self.db_file))
        self.system.bootstrap()

    def tearDown(self) -> None:
        self.temp_dir.cleanup()

    def test_production_sales_and_reports(self) -> None:
        product_id = self.system.add_product("Пломбир", "сливочное", 120.0, 200.0, unit="кг")
        milk = self.system.add_raw_material("Молоко", "л", 100.0, 20.0)
        sugar = self.system.add_raw_material("Сахар", "кг", 60.0, 10.0)

        self.system.set_recipe(product_id, [(milk, 1.5), (sugar, 0.4)])
        self.system.produce(product_id, 20.0, "Утренняя смена")
        self.system.sell(product_id, 8.0, "Розница")

        inventory = self.system.inventory_report()
        self.assertEqual(len(inventory), 1)
        self.assertAlmostEqual(inventory[0]["qty"], 12.0)

        sales = self.system.sales_analytics()
        self.assertEqual(len(sales), 1)
        self.assertAlmostEqual(sales[0]["total_sold"], 8.0)
        self.assertAlmostEqual(sales[0]["revenue"], 1600.0)

    def test_low_materials(self) -> None:
        self.system.add_raw_material("Вафельная крошка", "кг", 5.0, 5.0)
        low = self.system.low_materials_report()
        self.assertEqual(len(low), 1)
        self.assertEqual(low[0]["name"], "Вафельная крошка")


if __name__ == "__main__":
    unittest.main()
