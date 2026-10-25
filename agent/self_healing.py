"""
Self-Healing Error Recovery Engine
When dynamic CSS selectors break (e.g. hashed class names in SPAs), this module executes
a 4-tier fallback: ARIA labels -> Semantic Inner Text -> Attribute Heuristics -> Bounding Box Spatial Coordinates.
"""

from typing import Dict, Any, Optional
import asyncio
from playwright.async_api import Page, Locator


class SelfHealingLocator:
    """
    Intelligent resilient locator execution for Playwright actions.
    """

    def __init__(self, page: Page):
        self.page = page

    async def execute_resilient_click(
        self,
        element_meta: Dict[str, Any],
        broken_selector_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Attempts to click an element through 4 recovery tiers.
        """
        target_selector = broken_selector_override or element_meta.get("selector", "")
        text = element_meta.get("text", "")
        aria_label = element_meta.get("ariaLabel", "")
        role = element_meta.get("role", "")
        tag = element_meta.get("tag", "")
        bbox = element_meta.get("bbox", {})

        diagnostics = {
            "initial_selector": target_selector,
            "recovered": False,
            "recovery_tier": None,
            "error_reason": None
        }

        # --- Tier 0: Direct Primary Selector ---
        try:
            loc = self.page.locator(target_selector).first
            await loc.wait_for(state="visible", timeout=1200)
            await loc.click(timeout=1500)
            diagnostics["recovered"] = True
            diagnostics["recovery_tier"] = "Tier 0 (Primary Selector Direct Hit)"
            return diagnostics
        except Exception as e:
            diagnostics["error_reason"] = f"Primary selector failed: {str(e)[:80]}..."

        # --- Tier 1: ARIA Label / Role Matching ---
        if aria_label:
            try:
                loc = self.page.get_by_label(aria_label).first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.click(timeout=1500)
                    diagnostics["recovered"] = True
                    diagnostics["recovery_tier"] = f"Tier 1 (ARIA Label Fallback: '{aria_label}')"
                    return diagnostics
            except Exception:
                pass

        if role and text:
            try:
                # Playwright role + name locator
                loc = self.page.get_by_role(role, name=text).first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.click(timeout=1500)
                    diagnostics["recovered"] = True
                    diagnostics["recovery_tier"] = f"Tier 1 (Role+Name Fallback: role={role}, name='{text}')"
                    return diagnostics
            except Exception:
                pass

        # --- Tier 2: Inner Text Semantic Matching ---
        if text:
            try:
                loc = self.page.get_by_text(text, exact=False).first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.click(timeout=1500)
                    diagnostics["recovered"] = True
                    diagnostics["recovery_tier"] = f"Tier 2 (Inner Text Semantics: '{text}')"
                    return diagnostics
            except Exception:
                pass

        # --- Tier 3: Attribute Heuristics (placeholder, name) ---
        placeholder = element_meta.get("placeholder")
        if placeholder:
            try:
                loc = self.page.get_by_placeholder(placeholder).first
                if await loc.count() > 0 and await loc.is_visible():
                    await loc.click(timeout=1500)
                    diagnostics["recovered"] = True
                    diagnostics["recovery_tier"] = f"Tier 3 (Placeholder: '{placeholder}')"
                    return diagnostics
            except Exception:
                pass

        # --- Tier 4: Visual Bounding Box Coordinates (Spatial Click) ---
        if bbox and bbox.get("width", 0) > 0 and bbox.get("height", 0) > 0:
            try:
                cx = bbox["x"] + (bbox["width"] / 2)
                cy = bbox["y"] + (bbox["height"] / 2)
                await self.page.mouse.click(cx, cy)
                diagnostics["recovered"] = True
                diagnostics["recovery_tier"] = f"Tier 4 (Spatial Bounding Box: ({cx}, {cy}))"
                return diagnostics
            except Exception as e:
                diagnostics["error_reason"] = f"Spatial click failed: {str(e)}"

        diagnostics["recovered"] = False
        diagnostics["recovery_tier"] = "Exhausted all recovery tiers"
        return diagnostics

    async def execute_resilient_fill(
        self,
        element_meta: Dict[str, Any],
        value: str,
        broken_selector_override: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Resiliently fills an input field using multi-tier recovery.
        """
        target_selector = broken_selector_override or element_meta.get("selector", "")
        placeholder = element_meta.get("placeholder", "")
        name = element_meta.get("name", "")
        aria_label = element_meta.get("ariaLabel", "")
        bbox = element_meta.get("bbox", {})

        diagnostics = {
            "initial_selector": target_selector,
            "recovered": False,
            "recovery_tier": None
        }

        # Tier 0: Direct
        try:
            loc = self.page.locator(target_selector).first
            await loc.wait_for(state="visible", timeout=1200)
            await loc.fill(value, timeout=1500)
            diagnostics["recovered"] = True
            diagnostics["recovery_tier"] = "Tier 0 (Primary Selector Direct)"
            return diagnostics
        except Exception:
            pass

        # Tier 1: Placeholder
        if placeholder:
            try:
                loc = self.page.get_by_placeholder(placeholder).first
                if await loc.count() > 0:
                    await loc.fill(value)
                    diagnostics["recovered"] = True
                    diagnostics["recovery_tier"] = f"Tier 1 (Placeholder: '{placeholder}')"
                    return diagnostics
            except Exception:
                pass

        # Tier 2: ARIA / Label
        if aria_label:
            try:
                loc = self.page.get_by_label(aria_label).first
                if await loc.count() > 0:
                    await loc.fill(value)
                    diagnostics["recovered"] = True
                    diagnostics["recovery_tier"] = f"Tier 2 (ARIA Label: '{aria_label}')"
                    return diagnostics
            except Exception:
                pass

        # Tier 3: Spatial focus + keyboard type
        if bbox and bbox.get("width", 0) > 0:
            try:
                cx = bbox["x"] + (bbox["width"] / 2)
                cy = bbox["y"] + (bbox["height"] / 2)
                await self.page.mouse.click(cx, cy)
                await asyncio.sleep(0.1)
                await self.page.keyboard.type(value)
                diagnostics["recovered"] = True
                diagnostics["recovery_tier"] = f"Tier 3 (Spatial Focus + Keyboard Type: ({cx}, {cy}))"
                return diagnostics
            except Exception:
                pass

        diagnostics["recovered"] = False
        diagnostics["recovery_tier"] = "Failed all tiers"
        return diagnostics
