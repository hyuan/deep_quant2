"""Tests for trigger system."""

import unittest
from strategy.trigger_system import TriggerSystem, Trigger, TriggerAction, TriggerValidationError


class TestTriggerSystem(unittest.TestCase):
    """Test cases for the TriggerSystem class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.trigger_system = TriggerSystem()
    
    def test_add_trigger(self):
        """Test adding a trigger."""
        action = TriggerAction(name="buy", type="TradeAction", parameters={})
        trigger = Trigger(name="test_trigger", condition="close > 100", actions=[action])
        
        self.trigger_system.add_trigger(trigger)
        self.assertIn("test_trigger", self.trigger_system.triggers.keys())
    
    def test_add_duplicate_trigger(self):
        """Test adding duplicate trigger names."""
        action = TriggerAction(name="buy", type="TradeAction", parameters={})
        trigger1 = Trigger(name="test_trigger", condition="close > 100", actions=[action])
        trigger2 = Trigger(name="test_trigger", condition="close < 100", actions=[action])
        
        self.trigger_system.add_trigger(trigger1)
        
        with self.assertRaises(TriggerValidationError):
            self.trigger_system.add_trigger(trigger2)
    
    def test_remove_trigger(self):
        """Test removing a trigger."""
        action = TriggerAction(name="buy", type="TradeAction", parameters={})
        trigger = Trigger(name="test_trigger", condition="close > 100", actions=[action])
        
        self.trigger_system.add_trigger(trigger)
        self.trigger_system.remove_trigger("test_trigger")
        self.assertNotIn("test_trigger", self.trigger_system.triggers.keys())
    
    def test_remove_nonexistent_trigger(self):
        """Test removing a trigger that doesn't exist."""
        with self.assertRaises(TriggerValidationError):
            self.trigger_system.remove_trigger("nonexistent")
    
    def test_enable_disable_trigger(self):
        """Test enabling and disabling triggers."""
        action = TriggerAction(name="buy", type="TradeAction", parameters={})
        trigger = Trigger(name="test_trigger", condition="close > 100", actions=[action])
        
        self.trigger_system.add_trigger(trigger)
        
        # Initially enabled
        self.assertTrue(trigger.enabled)
        
        # Disable
        self.trigger_system.disable_trigger("test_trigger")
        self.assertFalse(trigger.enabled)
        
        # Enable
        self.trigger_system.enable_trigger("test_trigger")
        self.assertTrue(trigger.enabled)
    
    def test_get_active_triggers(self):
        """Test getting only enabled triggers."""
        action = TriggerAction(name="buy", type="TradeAction", parameters={})
        trigger1 = Trigger(name="trigger1", condition="close > 100", actions=[action])
        trigger2 = Trigger(name="trigger2", condition="close < 100", actions=[action])
        
        self.trigger_system.add_trigger(trigger1)
        self.trigger_system.add_trigger(trigger2)
        
        # Both enabled initially
        self.assertEqual(len(self.trigger_system.get_active_triggers()), 2)
        
        # Disable one
        self.trigger_system.disable_trigger("trigger1")
        active = self.trigger_system.get_active_triggers()
        self.assertEqual(len(active), 1)
        self.assertEqual(active[0].name, "trigger2")
    
    def test_validate_condition_syntax(self):
        """Test condition validation."""
        # Valid condition
        self.trigger_system.validate_condition("close > 100")
        
        # Invalid condition
        with self.assertRaises(TriggerValidationError):
            self.trigger_system.validate_condition("close >")
    
    def test_trigger_with_multiple_actions(self):
        """Test triggers with multiple actions."""
        action1 = TriggerAction(name="buy", type="TradeAction", parameters={})
        action2 = TriggerAction(name="stop_loss", type="TradeAction", parameters={})
        trigger = Trigger(
            name="test_trigger",
            condition="close > 100",
            actions=[action1, action2]
        )
        
        self.trigger_system.add_trigger(trigger)
        self.assertEqual(len(trigger.actions), 2)


if __name__ == '__main__':
    unittest.main()
