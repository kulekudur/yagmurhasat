"""
Economic Analysis Module
Calculates costs, savings, and ROI for the rainwater harvesting system
"""

import numpy as np
from typing import Dict
import config


class EconomicAnalyzer:
    """
    Analyzes the economic viability of a rainwater harvesting system.
    
    Metrics:
    - Water savings (liters and cost)
    - System costs (installation, maintenance)
    - Return on Investment (ROI)
    - Payback period
    """
    
    def __init__(
        self,
        water_price: float = config.WATER_PRICE,
        tank_cost: float = config.TANK_COST,
        maintenance_cost_annual: float = config.MAINTENANCE_COST,
        installation_cost: float = 2000
    ):
        """
        Initialize economic analyzer.
        
        Args:
            water_price: Price per liter of water (₺)
            tank_cost: Cost of storage tank (₺)
            maintenance_cost_annual: Annual maintenance cost (₺)
            installation_cost: Installation/setup cost (₺)
        """
        self.water_price = water_price
        self.tank_cost = tank_cost
        self.maintenance_cost_annual = maintenance_cost_annual
        self.installation_cost = installation_cost
        
    def calculate_water_savings(
        self,
        water_collected: float,
        water_consumed_from_tank: float
    ) -> Dict[str, float]:
        """
        Calculate water savings from rainwater harvesting.
        
        Args:
            water_collected: Total water collected (liters)
            water_consumed_from_tank: Water actually used from tank (liters)
            
        Returns:
            Dictionary with savings metrics
        """
        savings_liters = water_consumed_from_tank
        savings_cost = savings_liters * self.water_price
        
        if water_collected > 0:
            utilization_rate = (water_consumed_from_tank / water_collected) * 100
        else:
            utilization_rate = 0
        
        return {
            'water_saved_liters': savings_liters,
            'cost_saved': savings_cost,
            'utilization_rate': utilization_rate,
            'collected_liters': water_collected
        }
    
    def calculate_system_costs(self, years: int = 1) -> Dict[str, float]:
        """
        Calculate total system costs.
        
        Args:
            years: Number of years to calculate for
            
        Returns:
            Dictionary with cost breakdown
        """
        total_cost = self.installation_cost + self.tank_cost
        maintenance_total = self.maintenance_cost_annual * years
        total_cost += maintenance_total
        
        return {
            'installation_cost': self.installation_cost,
            'tank_cost': self.tank_cost,
            'maintenance_annual': self.maintenance_cost_annual,
            'maintenance_total': maintenance_total,
            'total_cost': total_cost,
            'cost_per_year': total_cost / years if years > 0 else 0
        }
    
    def calculate_roi(
        self,
        water_collected: float,
        water_consumed_from_tank: float,
        years: int = 1
    ) -> Dict[str, float]:
        """
        Calculate Return on Investment (ROI).
        
        ROI% = (savings - costs) / costs * 100
        
        Args:
            water_collected: Total water collected (liters)
            water_consumed_from_tank: Water used from tank (liters)
            years: Analysis period in years
            
        Returns:
            Dictionary with ROI metrics
        """
        savings = self.calculate_water_savings(water_collected, water_consumed_from_tank)
        costs = self.calculate_system_costs(years)
        
        total_savings = savings['cost_saved']
        total_cost = costs['total_cost']
        
        if total_cost > 0:
            roi_percentage = ((total_savings - total_cost) / total_cost) * 100
            net_benefit = total_savings - total_cost
        else:
            roi_percentage = 0
            net_benefit = total_savings
        
        payback_period = self._calculate_payback_period(
            annual_savings=total_savings / years if years > 0 else 0,
            total_cost=total_cost
        )
        
        return {
            'roi_percentage': roi_percentage,
            'net_benefit': net_benefit,
            'payback_period_years': payback_period,
            'annual_savings': total_savings / years if years > 0 else 0,
            'total_savings': total_savings,
            'total_investment': total_cost,
            'break_even': total_savings >= total_cost
        }
    
    def _calculate_payback_period(self, annual_savings: float, total_cost: float) -> float:
        """
        Calculate payback period in years.
        
        Args:
            annual_savings: Annual cost savings (₺)
            total_cost: Total system cost (₺)
            
        Returns:
            Payback period in years (or -1 if not achievable)
        """
        if annual_savings <= 0:
            return -1  # Never pays back
        
        return total_cost / annual_savings
    
    def get_breakeven_analysis(
        self,
        annual_water_collection: float
    ) -> Dict[str, float]:
        """
        Analyze breakeven point (when savings equal costs).
        
        Args:
            annual_water_collection: Expected annual water collection (liters)
            
        Returns:
            Dictionary with breakeven metrics
        """
        annual_value = annual_water_collection * self.water_price
        costs = self.calculate_system_costs(years=1)
        
        breakeven_cost = costs['total_cost']
        if annual_value > 0:
            years_to_breakeven = breakeven_cost / annual_value
        else:
            years_to_breakeven = float('inf')
        
        return {
            'annual_water_value': annual_value,
            'system_cost': breakeven_cost,
            'years_to_breakeven': years_to_breakeven,
            'economically_viable': years_to_breakeven < 20  # Typical system lifespan
        }
    
    def sensitivity_analysis(
        self,
        annual_water_collection: float,
        price_range: tuple = (0.3, 0.7)
    ) -> Dict[str, Dict[str, float]]:
        """
        Perform sensitivity analysis on water price.
        
        Args:
            annual_water_collection: Expected annual collection (liters)
            price_range: Tuple of (min_price, max_price)
            
        Returns:
            Dictionary with ROI at different price points
        """
        scenarios = {}
        original_price = self.water_price
        
        price_points = np.linspace(price_range[0], price_range[1], 5)
        
        for price in price_points:
            self.water_price = price
            roi = self.calculate_roi(
                water_collected=annual_water_collection,
                water_consumed_from_tank=annual_water_collection * 0.8,  # Assume 80% utilization
                years=1
            )
            scenarios[f'{price:.2f}_per_liter'] = roi
        
        self.water_price = original_price  # Restore original price
        return scenarios
    
    def get_annual_summary(
        self,
        water_collected: float,
        water_consumed: float,
        worker_count: int
    ) -> Dict:
        """
        Generate comprehensive annual economic summary.
        
        Args:
            water_collected: Annual water collected (liters)
            water_consumed: Annual water consumed from tank (liters)
            worker_count: Number of workers
            
        Returns:
            Comprehensive summary dictionary
        """
        savings = self.calculate_water_savings(water_collected, water_consumed)
        costs = self.calculate_system_costs(years=1)
        roi = self.calculate_roi(water_collected, water_consumed, years=1)
        breakeven = self.get_breakeven_analysis(water_collected)
        
        return {
            'overview': {
                'year': 2024,
                'worker_count': worker_count,
            },
            'water_metrics': {
                'collected_liters': savings['collected_liters'],
                'consumed_liters': savings['water_saved_liters'],
                'utilization_rate': savings['utilization_rate']
            },
            'financial': {
                'cost_saved': savings['cost_saved'],
                'total_investment': costs['total_cost'],
                'net_benefit': roi['net_benefit'],
                'roi_percentage': roi['roi_percentage'],
                'payback_years': roi['payback_period_years']
            },
            'breakeven': breakeven
        }
