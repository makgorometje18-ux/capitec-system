"""
Card Counter Module - Calculates SIM and Bank card totals.
"""

from src.models.models import CardStatistics, Workbook
from src.utils.logger import get_logger


class CardCounter:
    """
    Calculates card statistics based on order data.
    
    Computes SIM and Bank card totals using configurable
    multipliers (default: SIM=200, Bank=300).
    """

    def __init__(self, sim_multiplier: int = 200, bank_multiplier: int = 300) -> None:
        """
        Initialize the Card Counter.

        Args:
            sim_multiplier: Cards per SIM order (default: 200).
            bank_multiplier: Cards per Bank order (default: 300).
        """
        self.logger = get_logger()
        self.sim_multiplier = sim_multiplier
        self.bank_multiplier = bank_multiplier

    def count_cards(self, workbook: Workbook) -> CardStatistics:
        """
        Count cards from workbook data.
        
        Args:
            workbook: The Workbook object.
            
        Returns:
            CardStatistics with calculated totals.
        """
        stats = CardStatistics()
        try:
            self.logger.info("Counting cards from Workbook model is not implemented; returning zeros")
            return stats
        except Exception as e:
            self.logger.error(f"Error counting cards: {e}")
            return stats

    def count_cards_from_loader(self, loader, sheet_name: str) -> CardStatistics:
        """Count cards using a WorkbookLoader and sheet name.

        This is used by the ReconciliationEngine to compute SIM/Bank totals.
        """
        stats = CardStatistics()
        try:
            rows = loader.get_data_rows(sheet_name)
            if not rows:
                return stats

            for row in rows:
                raw_card_type = row.get('Card_Type', {}).get('value') or ''
                card_type = str(raw_card_type).strip().upper()
                no_of_batches = row.get('No_of_Batches', {}).get('value')
                try:
                    orders = int(no_of_batches)
                except Exception:
                    if no_of_batches is None or str(no_of_batches).strip() == '':
                        orders = 0
                    else:
                        self.logger.warning(
                            "Invalid No_of_Batches '%s' on row %s; treating as 0",
                            no_of_batches,
                            row.get('No_of_Batches', {}).get('row')
                        )
                        orders = 0

                if card_type == 'SIM':
                    stats.sim_orders += orders
                    stats.sim_cards += self.calculate_sim_cards(orders)
                elif card_type == 'DMCCLS':
                    stats.bank_orders += orders
                    stats.bank_cards += self.calculate_bank_cards(orders)
                else:
                    self.logger.warning(
                        "Unrecognized Card_Type '%s' on row %s; ignoring for summary counts",
                        raw_card_type,
                        row.get('Card_Type', {}).get('row')
                    )

            stats.total_orders = stats.sim_orders + stats.bank_orders
            stats.total_cards = stats.sim_cards + stats.bank_cards

            # Log totals per user request
            self.logger.info("CardCounter totals: SIM Orders=%d, SIM Cards=%d, Bank Orders=%d, Bank Cards=%d",
                             stats.sim_orders, stats.sim_cards, stats.bank_orders, stats.bank_cards)
            return stats

        except Exception as e:
            self.logger.error(f"Error counting cards from loader: {e}")
            return stats

    def calculate_sim_cards(self, orders: int) -> int:
        """
        Calculate total SIM cards from orders.
        
        Args:
            orders: Number of SIM orders.
            
        Returns:
            Total SIM cards.
        """
        return orders * self.sim_multiplier

    def calculate_bank_cards(self, orders: int) -> int:
        """
        Calculate total Bank cards from orders.
        
        Args:
            orders: Number of Bank orders.
            
        Returns:
            Total Bank cards.
        """
        return orders * self.bank_multiplier
