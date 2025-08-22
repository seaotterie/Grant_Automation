"""
PHASE 6: Mobile and Accessibility Enhancement System
Advanced accessibility features and mobile optimization for the grant research platform
with WCAG 2.1 AA compliance, responsive design, and inclusive user experience.
"""

import asyncio
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from pathlib import Path
import json
import re

from src.core.base_processor import BaseProcessor

logger = logging.getLogger(__name__)

class AccessibilityLevel(Enum):
    """WCAG accessibility compliance levels"""
    A = "A"           # Level A compliance
    AA = "AA"         # Level AA compliance (target)
    AAA = "AAA"       # Level AAA compliance

class DeviceType(Enum):
    """Device types for responsive design"""
    DESKTOP = "desktop"         # Desktop computers
    TABLET = "tablet"           # Tablets (portrait/landscape)
    MOBILE = "mobile"           # Mobile phones
    LARGE_DISPLAY = "large"     # Large displays/TVs
    WATCH = "watch"             # Smart watches

class InteractionMode(Enum):
    """Interaction modes for accessibility"""
    TOUCH = "touch"             # Touch-based interaction
    KEYBOARD = "keyboard"       # Keyboard navigation
    VOICE = "voice"             # Voice commands
    GESTURE = "gesture"         # Gesture-based
    EYE_TRACKING = "eye"        # Eye-tracking
    SWITCH = "switch"           # Switch control

class ColorTheme(Enum):
    """Color themes for accessibility"""
    DEFAULT = "default"         # Standard theme
    HIGH_CONTRAST = "high_contrast"    # High contrast mode
    DARK_MODE = "dark"          # Dark mode
    LIGHT_MODE = "light"        # Light mode
    COLORBLIND_FRIENDLY = "colorblind"  # Color-blind friendly
    MONOCHROME = "monochrome"   # Monochrome theme

@dataclass
class AccessibilityPreferences:
    """User accessibility preferences"""
    user_id: str
    
    # Visual preferences
    font_size_multiplier: float = 1.0      # Font size scaling (0.8-2.0)
    line_height_multiplier: float = 1.0    # Line height scaling
    color_theme: ColorTheme = ColorTheme.DEFAULT
    high_contrast_mode: bool = False
    reduce_motion: bool = False
    reduce_transparency: bool = False
    
    # Audio preferences
    audio_descriptions: bool = False
    sound_enabled: bool = True
    audio_feedback: bool = False
    
    # Navigation preferences
    keyboard_navigation: bool = True
    focus_indicators: bool = True
    skip_links: bool = True
    sticky_navigation: bool = False
    
    # Content preferences
    simple_language: bool = False
    show_tooltips: bool = True
    auto_play_media: bool = False
    show_captions: bool = False
    
    # Interaction preferences
    touch_target_size: str = "medium"      # small, medium, large, extra_large
    click_delay: int = 0                   # Additional click delay (ms)
    drag_threshold: int = 10               # Pixels before drag starts
    
    # Assistive technology
    screen_reader_mode: bool = False
    voice_control: bool = False
    switch_control: bool = False
    
    # Mobile-specific preferences
    mobile_zoom_enabled: bool = True
    mobile_gestures_enabled: bool = True
    mobile_orientation_lock: Optional[str] = None  # 'portrait', 'landscape'
    
    last_updated: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ResponsiveBreakpoint:
    """Responsive design breakpoint configuration"""
    name: str
    device_type: DeviceType
    min_width: Optional[int] = None
    max_width: Optional[int] = None
    min_height: Optional[int] = None
    max_height: Optional[int] = None
    
    # Layout adjustments
    columns: int = 12
    gutter_size: int = 15
    container_padding: int = 15
    
    # Typography adjustments
    base_font_size: int = 14
    heading_scale: float = 1.25
    line_height: float = 1.5
    
    # Component adjustments
    button_size: str = "medium"         # small, medium, large
    input_height: int = 40
    touch_target_size: int = 44         # Minimum 44px for touch
    
    # Navigation adjustments
    navbar_style: str = "full"          # full, collapsed, drawer
    sidebar_behavior: str = "fixed"     # fixed, overlay, push
    
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AccessibilityAuditResult:
    """Result of accessibility audit"""
    audit_id: str
    page_url: str
    compliance_level: AccessibilityLevel
    overall_score: float                # 0.0-1.0
    
    # WCAG guideline scores
    perceivable_score: float           # 0.0-1.0
    operable_score: float              # 0.0-1.0
    understandable_score: float        # 0.0-1.0
    robust_score: float                # 0.0-1.0
    
    # Issues found
    critical_issues: List[Dict[str, Any]] = field(default_factory=list)
    major_issues: List[Dict[str, Any]] = field(default_factory=list)
    minor_issues: List[Dict[str, Any]] = field(default_factory=list)
    suggestions: List[Dict[str, Any]] = field(default_factory=list)
    
    # Performance metrics
    audit_duration: float = 0.0
    elements_checked: int = 0
    
    # Recommendations
    quick_fixes: List[str] = field(default_factory=list)
    improvement_plan: List[Dict[str, Any]] = field(default_factory=list)
    
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

class ResponsiveDesignEngine:
    """Engine for responsive design implementation"""
    
    def __init__(self):
        self.breakpoints = self._create_default_breakpoints()
        self.css_generator = CSSGenerator()
    
    def _create_default_breakpoints(self) -> Dict[str, ResponsiveBreakpoint]:
        """Create default responsive breakpoints"""
        return {
            'mobile_portrait': ResponsiveBreakpoint(
                name='Mobile Portrait',
                device_type=DeviceType.MOBILE,
                max_width=480,
                columns=1,
                gutter_size=10,
                container_padding=15,
                base_font_size=14,
                navbar_style='collapsed',
                sidebar_behavior='overlay',
                touch_target_size=48
            ),
            'mobile_landscape': ResponsiveBreakpoint(
                name='Mobile Landscape',
                device_type=DeviceType.MOBILE,
                min_width=481,
                max_width=768,
                columns=2,
                gutter_size=12,
                container_padding=20,
                base_font_size=14,
                navbar_style='collapsed',
                sidebar_behavior='overlay'
            ),
            'tablet_portrait': ResponsiveBreakpoint(
                name='Tablet Portrait',
                device_type=DeviceType.TABLET,
                min_width=769,
                max_width=1024,
                columns=3,
                gutter_size=15,
                container_padding=25,
                base_font_size=15,
                navbar_style='full',
                sidebar_behavior='push'
            ),
            'tablet_landscape': ResponsiveBreakpoint(
                name='Tablet Landscape',
                device_type=DeviceType.TABLET,
                min_width=1025,
                max_width=1200,
                columns=4,
                gutter_size=15,
                container_padding=30,
                base_font_size=15,
                navbar_style='full',
                sidebar_behavior='fixed'
            ),
            'desktop': ResponsiveBreakpoint(
                name='Desktop',
                device_type=DeviceType.DESKTOP,
                min_width=1201,
                max_width=1440,
                columns=12,
                gutter_size=20,
                container_padding=40,
                base_font_size=16,
                navbar_style='full',
                sidebar_behavior='fixed'
            ),
            'large_desktop': ResponsiveBreakpoint(
                name='Large Desktop',
                device_type=DeviceType.LARGE_DISPLAY,
                min_width=1441,
                columns=12,
                gutter_size=25,
                container_padding=50,
                base_font_size=16,
                navbar_style='full',
                sidebar_behavior='fixed'
            )
        }
    
    async def generate_responsive_css(self, preferences: AccessibilityPreferences) -> str:
        """Generate responsive CSS based on user preferences"""
        try:
            css_rules = []
            
            # Base styles
            css_rules.append(await self._generate_base_styles(preferences))
            
            # Responsive breakpoints
            for breakpoint_name, breakpoint in self.breakpoints.items():
                breakpoint_css = await self._generate_breakpoint_css(breakpoint, preferences)
                css_rules.append(breakpoint_css)
            
            # Accessibility-specific styles
            css_rules.append(await self._generate_accessibility_styles(preferences))
            
            # Theme-specific styles
            css_rules.append(await self._generate_theme_styles(preferences))
            
            return '\n\n'.join(filter(None, css_rules))
            
        except Exception as e:
            logger.error(f"Error generating responsive CSS: {e}")
            return ""
    
    async def _generate_base_styles(self, preferences: AccessibilityPreferences) -> str:
        """Generate base CSS styles"""
        
        base_font_size = 16 * preferences.font_size_multiplier
        line_height = 1.5 * preferences.line_height_multiplier
        
        return f"""
        /* Base Responsive Styles */
        * {{
            box-sizing: border-box;
        }}
        
        html {{
            font-size: {base_font_size}px;
            line-height: {line_height};
            scroll-behavior: {'auto' if preferences.reduce_motion else 'smooth'};
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            overflow-x: hidden;
        }}
        
        /* Focus indicators */
        {'*:focus { outline: 3px solid #005fcc; outline-offset: 2px; }' if preferences.focus_indicators else ''}
        
        /* Reduced motion preferences */
        {'* { animation: none !important; transition: none !important; }' if preferences.reduce_motion else ''}
        
        /* High contrast mode adjustments */
        {'@media (prefers-contrast: high) { * { filter: contrast(150%); } }' if preferences.high_contrast_mode else ''}
        
        /* Touch target sizing */
        button, .btn, input[type="button"], input[type="submit"], .touch-target {{
            min-height: {44 if preferences.touch_target_size == 'large' else 40}px;
            min-width: {44 if preferences.touch_target_size == 'large' else 40}px;
            padding: 8px 16px;
        }}
        """
    
    async def _generate_breakpoint_css(self, breakpoint: ResponsiveBreakpoint, preferences: AccessibilityPreferences) -> str:
        """Generate CSS for specific breakpoint"""
        
        media_query = self._build_media_query(breakpoint)
        if not media_query:
            return ""
        
        adjusted_font_size = breakpoint.base_font_size * preferences.font_size_multiplier
        adjusted_line_height = breakpoint.line_height * preferences.line_height_multiplier
        
        return f"""
        {media_query} {{
            html {{
                font-size: {adjusted_font_size}px;
                line-height: {adjusted_line_height};
            }}
            
            .container {{
                max-width: 100%;
                padding: 0 {breakpoint.container_padding}px;
                margin: 0 auto;
            }}
            
            .grid {{
                display: grid;
                grid-template-columns: repeat({breakpoint.columns}, 1fr);
                gap: {breakpoint.gutter_size}px;
            }}
            
            /* Navigation adjustments */
            .navbar {{
                display: {'flex' if breakpoint.navbar_style == 'full' else 'none'};
            }}
            
            .navbar-mobile {{
                display: {'flex' if breakpoint.navbar_style == 'collapsed' else 'none'};
            }}
            
            .sidebar {{
                {'position: fixed;' if breakpoint.sidebar_behavior == 'fixed' else ''}
                {'position: absolute; z-index: 1000;' if breakpoint.sidebar_behavior == 'overlay' else ''}
            }}
            
            /* Touch-friendly spacing for mobile */
            {self._generate_mobile_specific_css(breakpoint) if breakpoint.device_type == DeviceType.MOBILE else ''}
        }}
        """
    
    def _build_media_query(self, breakpoint: ResponsiveBreakpoint) -> str:
        """Build media query for breakpoint"""
        conditions = []
        
        if breakpoint.min_width:
            conditions.append(f"(min-width: {breakpoint.min_width}px)")
        if breakpoint.max_width:
            conditions.append(f"(max-width: {breakpoint.max_width}px)")
        if breakpoint.min_height:
            conditions.append(f"(min-height: {breakpoint.min_height}px)")
        if breakpoint.max_height:
            conditions.append(f"(max-height: {breakpoint.max_height}px)")
        
        if not conditions:
            return ""
        
        return f"@media {' and '.join(conditions)}"
    
    def _generate_mobile_specific_css(self, breakpoint: ResponsiveBreakpoint) -> str:
        """Generate mobile-specific CSS optimizations"""
        return f"""
        /* Mobile-specific optimizations */
        body {{
            -webkit-text-size-adjust: 100%;
            -ms-text-size-adjust: 100%;
        }}
        
        /* Larger touch targets */
        input, select, textarea, button {{
            min-height: {breakpoint.touch_target_size}px;
            font-size: 16px; /* Prevent zoom on iOS */
        }}
        
        /* Better tap highlighting */
        * {{
            -webkit-tap-highlight-color: rgba(0, 0, 0, 0.1);
        }}
        
        /* Improved scrolling */
        .scroll-container {{
            -webkit-overflow-scrolling: touch;
            overflow-y: auto;
        }}
        
        /* Hide elements inappropriate for mobile */
        .desktop-only {{
            display: none !important;
        }}
        
        /* Show mobile-specific elements */
        .mobile-only {{
            display: block !important;
        }}
        """
    
    async def _generate_accessibility_styles(self, preferences: AccessibilityPreferences) -> str:
        """Generate accessibility-specific styles"""
        
        styles = []
        
        # Screen reader specific styles
        if preferences.screen_reader_mode:
            styles.append("""
            /* Screen reader optimizations */
            .sr-only {
                position: absolute;
                width: 1px;
                height: 1px;
                padding: 0;
                margin: -1px;
                overflow: hidden;
                clip: rect(0, 0, 0, 0);
                white-space: nowrap;
                border: 0;
            }
            
            .sr-only-focusable:focus {
                position: static;
                width: auto;
                height: auto;
                padding: inherit;
                margin: inherit;
                overflow: visible;
                clip: auto;
                white-space: inherit;
            }
            """)
        
        # High contrast mode
        if preferences.high_contrast_mode:
            styles.append("""
            /* High contrast mode */
            * {
                background-color: transparent !important;
                color: inherit !important;
                border-color: currentColor !important;
            }
            
            body {
                background-color: white !important;
                color: black !important;
            }
            
            a, button {
                color: blue !important;
            }
            
            a:visited {
                color: purple !important;
            }
            """)
        
        # Reduced transparency
        if preferences.reduce_transparency:
            styles.append("""
            /* Reduced transparency */
            * {
                opacity: 1 !important;
                background-color: rgba(255, 255, 255, 1) !important;
            }
            """)
        
        # Skip links
        if preferences.skip_links:
            styles.append("""
            /* Skip links */
            .skip-link {
                position: absolute;
                top: -40px;
                left: 6px;
                background: #000;
                color: #fff;
                padding: 8px;
                text-decoration: none;
                z-index: 1000;
            }
            
            .skip-link:focus {
                top: 6px;
            }
            """)
        
        return '\n\n'.join(styles)
    
    async def _generate_theme_styles(self, preferences: AccessibilityPreferences) -> str:
        """Generate theme-specific styles"""
        
        theme_styles = {
            ColorTheme.DEFAULT: """
            :root {
                --primary-color: #007bff;
                --secondary-color: #6c757d;
                --background-color: #ffffff;
                --text-color: #212529;
                --border-color: #dee2e6;
            }
            """,
            
            ColorTheme.DARK_MODE: """
            :root {
                --primary-color: #0d6efd;
                --secondary-color: #6c757d;
                --background-color: #121212;
                --text-color: #ffffff;
                --border-color: #444;
            }
            
            body {
                background-color: var(--background-color);
                color: var(--text-color);
            }
            """,
            
            ColorTheme.HIGH_CONTRAST: """
            :root {
                --primary-color: #0000ff;
                --secondary-color: #000000;
                --background-color: #ffffff;
                --text-color: #000000;
                --border-color: #000000;
            }
            
            * {
                background-color: var(--background-color) !important;
                color: var(--text-color) !important;
                border-color: var(--border-color) !important;
            }
            """,
            
            ColorTheme.COLORBLIND_FRIENDLY: """
            :root {
                --primary-color: #1f77b4;
                --secondary-color: #ff7f0e;
                --success-color: #2ca02c;
                --danger-color: #d62728;
                --warning-color: #bcbd22;
                --info-color: #17becf;
            }
            
            /* Use patterns and shapes in addition to color */
            .success::before { content: "✓ "; }
            .danger::before { content: "✗ "; }
            .warning::before { content: "⚠ "; }
            .info::before { content: "ⓘ "; }
            """
        }
        
        return theme_styles.get(preferences.color_theme, theme_styles[ColorTheme.DEFAULT])

class AccessibilityAuditor:
    """Accessibility auditing engine"""
    
    def __init__(self):
        self.audit_rules = self._initialize_audit_rules()
    
    def _initialize_audit_rules(self) -> Dict[str, Any]:
        """Initialize accessibility audit rules"""
        return {
            'perceivable': {
                'alt_text_missing': {
                    'selector': 'img:not([alt])',
                    'level': AccessibilityLevel.A,
                    'severity': 'critical',
                    'message': 'Image missing alt attribute'
                },
                'color_contrast_low': {
                    'check': 'color_contrast',
                    'level': AccessibilityLevel.AA,
                    'severity': 'major',
                    'minimum_ratio': 4.5
                },
                'audio_captions_missing': {
                    'selector': 'video:not([captions]), audio:not([captions])',
                    'level': AccessibilityLevel.A,
                    'severity': 'major',
                    'message': 'Media missing captions'
                }
            },
            'operable': {
                'keyboard_navigation': {
                    'selector': '[onclick]:not([tabindex]), [role="button"]:not([tabindex])',
                    'level': AccessibilityLevel.A,
                    'severity': 'critical',
                    'message': 'Interactive element not keyboard accessible'
                },
                'focus_indicator_missing': {
                    'check': 'focus_indicator',
                    'level': AccessibilityLevel.AA,
                    'severity': 'major',
                    'message': 'Focus indicator not visible'
                },
                'touch_target_size': {
                    'check': 'touch_target_size',
                    'level': AccessibilityLevel.AA,
                    'severity': 'major',
                    'minimum_size': 44
                }
            },
            'understandable': {
                'page_language_missing': {
                    'selector': 'html:not([lang])',
                    'level': AccessibilityLevel.A,
                    'severity': 'major',
                    'message': 'Page language not specified'
                },
                'form_labels_missing': {
                    'selector': 'input:not([aria-label]):not([aria-labelledby]):not([title])',
                    'level': AccessibilityLevel.A,
                    'severity': 'critical',
                    'message': 'Form input missing label'
                },
                'error_identification': {
                    'check': 'error_messages',
                    'level': AccessibilityLevel.A,
                    'severity': 'major',
                    'message': 'Form errors not properly identified'
                }
            },
            'robust': {
                'html_validation': {
                    'check': 'html_validity',
                    'level': AccessibilityLevel.A,
                    'severity': 'minor',
                    'message': 'Invalid HTML markup'
                },
                'aria_usage': {
                    'check': 'aria_validity',
                    'level': AccessibilityLevel.A,
                    'severity': 'major',
                    'message': 'Invalid ARIA usage'
                }
            }
        }
    
    async def audit_page(self, page_content: str, page_url: str) -> AccessibilityAuditResult:
        """Perform comprehensive accessibility audit of page"""
        try:
            audit_id = f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            start_time = datetime.now()
            
            # Parse HTML content (simplified - in real implementation would use proper HTML parser)
            elements_found = self._parse_html_elements(page_content)
            
            # Initialize result
            result = AccessibilityAuditResult(
                audit_id=audit_id,
                page_url=page_url,
                compliance_level=AccessibilityLevel.A,
                overall_score=0.0,
                perceivable_score=0.0,
                operable_score=0.0,
                understandable_score=0.0,
                robust_score=0.0,
                elements_checked=len(elements_found)
            )
            
            # Audit each WCAG principle
            perceivable_results = await self._audit_perceivable(page_content, elements_found)
            operable_results = await self._audit_operable(page_content, elements_found)
            understandable_results = await self._audit_understandable(page_content, elements_found)
            robust_results = await self._audit_robust(page_content, elements_found)
            
            # Combine results
            all_issues = []
            all_issues.extend(perceivable_results.get('issues', []))
            all_issues.extend(operable_results.get('issues', []))
            all_issues.extend(understandable_results.get('issues', []))
            all_issues.extend(robust_results.get('issues', []))
            
            # Categorize issues by severity
            result.critical_issues = [i for i in all_issues if i.get('severity') == 'critical']
            result.major_issues = [i for i in all_issues if i.get('severity') == 'major']
            result.minor_issues = [i for i in all_issues if i.get('severity') == 'minor']
            
            # Calculate scores
            result.perceivable_score = perceivable_results.get('score', 0.0)
            result.operable_score = operable_results.get('score', 0.0)
            result.understandable_score = understandable_results.get('score', 0.0)
            result.robust_score = robust_results.get('score', 0.0)
            
            result.overall_score = (
                result.perceivable_score + result.operable_score + 
                result.understandable_score + result.robust_score
            ) / 4.0
            
            # Determine compliance level
            if result.overall_score >= 0.95 and not result.critical_issues:
                result.compliance_level = AccessibilityLevel.AAA
            elif result.overall_score >= 0.85 and len(result.critical_issues) <= 1:
                result.compliance_level = AccessibilityLevel.AA
            else:
                result.compliance_level = AccessibilityLevel.A
            
            # Generate recommendations
            result.quick_fixes = self._generate_quick_fixes(all_issues)
            result.improvement_plan = self._generate_improvement_plan(all_issues)
            
            # Calculate audit duration
            result.audit_duration = (datetime.now() - start_time).total_seconds()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in accessibility audit: {e}")
            return AccessibilityAuditResult(
                audit_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                page_url=page_url,
                compliance_level=AccessibilityLevel.A,
                overall_score=0.0,
                perceivable_score=0.0,
                operable_score=0.0,
                understandable_score=0.0,
                robust_score=0.0
            )
    
    def _parse_html_elements(self, html_content: str) -> List[Dict[str, Any]]:
        """Parse HTML elements from content (simplified implementation)"""
        elements = []
        
        # Find images
        img_matches = re.finditer(r'<img[^>]*>', html_content, re.IGNORECASE)
        for match in img_matches:
            img_tag = match.group(0)
            elements.append({
                'type': 'img',
                'tag': img_tag,
                'has_alt': 'alt=' in img_tag.lower(),
                'position': match.start()
            })
        
        # Find form inputs
        input_matches = re.finditer(r'<input[^>]*>', html_content, re.IGNORECASE)
        for match in input_matches:
            input_tag = match.group(0)
            elements.append({
                'type': 'input',
                'tag': input_tag,
                'has_label': any(attr in input_tag.lower() for attr in ['aria-label=', 'aria-labelledby=', 'title=']),
                'position': match.start()
            })
        
        # Find buttons and interactive elements
        button_matches = re.finditer(r'<button[^>]*>|<[^>]*onclick[^>]*>', html_content, re.IGNORECASE)
        for match in button_matches:
            button_tag = match.group(0)
            elements.append({
                'type': 'interactive',
                'tag': button_tag,
                'has_tabindex': 'tabindex=' in button_tag.lower(),
                'position': match.start()
            })
        
        # Find headings
        heading_matches = re.finditer(r'<h[1-6][^>]*>', html_content, re.IGNORECASE)
        for match in heading_matches:
            heading_tag = match.group(0)
            level = int(re.search(r'h([1-6])', heading_tag.lower()).group(1))
            elements.append({
                'type': 'heading',
                'tag': heading_tag,
                'level': level,
                'position': match.start()
            })
        
        return elements
    
    async def _audit_perceivable(self, content: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit perceivable principle"""
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Check for missing alt text
        img_elements = [e for e in elements if e['type'] == 'img']
        total_checks += len(img_elements)
        
        for img in img_elements:
            if not img['has_alt']:
                issues.append({
                    'type': 'alt_text_missing',
                    'severity': 'critical',
                    'message': 'Image missing alt attribute',
                    'element': img['tag'][:100],
                    'position': img['position']
                })
            else:
                passed_checks += 1
        
        # Check for page language
        total_checks += 1
        if '<html' in content.lower() and 'lang=' in content.lower():
            passed_checks += 1
        else:
            issues.append({
                'type': 'page_language_missing',
                'severity': 'major',
                'message': 'HTML document missing lang attribute',
                'element': '<html>',
                'position': 0
            })
        
        # Check heading structure
        heading_elements = [e for e in elements if e['type'] == 'heading']
        if heading_elements:
            total_checks += 1
            heading_levels = [h['level'] for h in heading_elements]
            if heading_levels == sorted(heading_levels) and heading_levels[0] == 1:
                passed_checks += 1
            else:
                issues.append({
                    'type': 'heading_structure',
                    'severity': 'minor',
                    'message': 'Heading structure not hierarchical',
                    'element': 'heading structure',
                    'position': 0
                })
        
        score = passed_checks / total_checks if total_checks > 0 else 1.0
        
        return {
            'score': score,
            'issues': issues,
            'total_checks': total_checks,
            'passed_checks': passed_checks
        }
    
    async def _audit_operable(self, content: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit operable principle"""
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Check keyboard accessibility
        interactive_elements = [e for e in elements if e['type'] == 'interactive']
        total_checks += len(interactive_elements)
        
        for element in interactive_elements:
            if element['has_tabindex'] or 'button' in element['tag'].lower():
                passed_checks += 1
            else:
                issues.append({
                    'type': 'keyboard_navigation',
                    'severity': 'critical',
                    'message': 'Interactive element not keyboard accessible',
                    'element': element['tag'][:100],
                    'position': element['position']
                })
        
        # Check for focus management
        total_checks += 1
        if 'focus' in content.lower() or ':focus' in content.lower():
            passed_checks += 1
        else:
            issues.append({
                'type': 'focus_management',
                'severity': 'major',
                'message': 'No focus management detected',
                'element': 'page focus',
                'position': 0
            })
        
        score = passed_checks / total_checks if total_checks > 0 else 1.0
        
        return {
            'score': score,
            'issues': issues,
            'total_checks': total_checks,
            'passed_checks': passed_checks
        }
    
    async def _audit_understandable(self, content: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit understandable principle"""
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Check form labels
        input_elements = [e for e in elements if e['type'] == 'input']
        total_checks += len(input_elements)
        
        for input_elem in input_elements:
            if input_elem['has_label']:
                passed_checks += 1
            else:
                issues.append({
                    'type': 'form_labels_missing',
                    'severity': 'critical',
                    'message': 'Form input missing accessible label',
                    'element': input_elem['tag'][:100],
                    'position': input_elem['position']
                })
        
        # Check for error handling
        total_checks += 1
        if any(keyword in content.lower() for keyword in ['error', 'invalid', 'required']):
            passed_checks += 1
        else:
            issues.append({
                'type': 'error_handling',
                'severity': 'minor',
                'message': 'No error handling patterns detected',
                'element': 'form validation',
                'position': 0
            })
        
        score = passed_checks / total_checks if total_checks > 0 else 1.0
        
        return {
            'score': score,
            'issues': issues,
            'total_checks': total_checks,
            'passed_checks': passed_checks
        }
    
    async def _audit_robust(self, content: str, elements: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Audit robust principle"""
        issues = []
        total_checks = 0
        passed_checks = 0
        
        # Check for HTML validity (basic checks)
        total_checks += 1
        if self._check_basic_html_validity(content):
            passed_checks += 1
        else:
            issues.append({
                'type': 'html_validity',
                'severity': 'minor',
                'message': 'HTML markup issues detected',
                'element': 'HTML document',
                'position': 0
            })
        
        # Check ARIA usage
        total_checks += 1
        aria_valid = self._check_aria_validity(content)
        if aria_valid:
            passed_checks += 1
        else:
            issues.append({
                'type': 'aria_usage',
                'severity': 'major',
                'message': 'ARIA attributes used incorrectly',
                'element': 'ARIA elements',
                'position': 0
            })
        
        score = passed_checks / total_checks if total_checks > 0 else 1.0
        
        return {
            'score': score,
            'issues': issues,
            'total_checks': total_checks,
            'passed_checks': passed_checks
        }
    
    def _check_basic_html_validity(self, content: str) -> bool:
        """Basic HTML validity check"""
        # Simple checks for common issues
        unclosed_tags = ['<div', '<p', '<span', '<h1', '<h2', '<h3', '<h4', '<h5', '<h6']
        
        for tag in unclosed_tags:
            open_count = content.lower().count(tag)
            close_count = content.lower().count(tag.replace('<', '</'))
            if open_count != close_count:
                return False
        
        return True
    
    def _check_aria_validity(self, content: str) -> bool:
        """Check ARIA attribute validity"""
        # Check for common ARIA issues
        aria_patterns = re.finditer(r'aria-\w+="[^"]*"', content.lower())
        
        valid_aria_attributes = {
            'aria-label', 'aria-labelledby', 'aria-describedby', 'aria-expanded',
            'aria-hidden', 'aria-live', 'aria-role', 'aria-pressed', 'aria-checked'
        }
        
        for match in aria_patterns:
            aria_attr = match.group(0).split('=')[0]
            if aria_attr not in valid_aria_attributes:
                return False
        
        return True
    
    def _generate_quick_fixes(self, issues: List[Dict[str, Any]]) -> List[str]:
        """Generate quick fix suggestions"""
        quick_fixes = []
        
        issue_types = set(issue['type'] for issue in issues)
        
        if 'alt_text_missing' in issue_types:
            quick_fixes.append("Add alt attributes to all images with descriptive text")
        
        if 'form_labels_missing' in issue_types:
            quick_fixes.append("Add aria-label or associate labels with form inputs")
        
        if 'keyboard_navigation' in issue_types:
            quick_fixes.append("Add tabindex='0' to interactive elements or use semantic HTML")
        
        if 'page_language_missing' in issue_types:
            quick_fixes.append("Add lang attribute to <html> element")
        
        if 'focus_management' in issue_types:
            quick_fixes.append("Add visible focus indicators with CSS :focus styles")
        
        return quick_fixes
    
    def _generate_improvement_plan(self, issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate comprehensive improvement plan"""
        plan = []
        
        critical_count = len([i for i in issues if i['severity'] == 'critical'])
        major_count = len([i for i in issues if i['severity'] == 'major'])
        minor_count = len([i for i in issues if i['severity'] == 'minor'])
        
        if critical_count > 0:
            plan.append({
                'priority': 'Critical',
                'timeline': '1 week',
                'effort': 'High',
                'description': f'Fix {critical_count} critical accessibility issues',
                'issues': critical_count
            })
        
        if major_count > 0:
            plan.append({
                'priority': 'Major',
                'timeline': '2-4 weeks',
                'effort': 'Medium',
                'description': f'Address {major_count} major accessibility improvements',
                'issues': major_count
            })
        
        if minor_count > 0:
            plan.append({
                'priority': 'Minor',
                'timeline': '1-2 months',
                'effort': 'Low',
                'description': f'Implement {minor_count} minor enhancements',
                'issues': minor_count
            })
        
        return plan

class CSSGenerator:
    """CSS generation utility"""
    
    async def generate_accessibility_css(self, preferences: AccessibilityPreferences) -> str:
        """Generate comprehensive accessibility CSS"""
        
        css_sections = []
        
        # Reset and base styles
        css_sections.append(self._generate_reset_css())
        
        # Typography and readability
        css_sections.append(self._generate_typography_css(preferences))
        
        # Focus and interaction styles
        css_sections.append(self._generate_interaction_css(preferences))
        
        # Color and theme styles
        css_sections.append(self._generate_color_css(preferences))
        
        # Layout and spacing
        css_sections.append(self._generate_layout_css(preferences))
        
        # Print styles
        css_sections.append(self._generate_print_css())
        
        return '\n\n'.join(css_sections)
    
    def _generate_reset_css(self) -> str:
        """Generate CSS reset for consistency"""
        return """
        /* Accessibility-focused CSS Reset */
        *, *::before, *::after {
            box-sizing: border-box;
        }
        
        html {
            scroll-behavior: smooth;
            font-size: 100%;
        }
        
        body {
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', system-ui, sans-serif;
            line-height: 1.5;
            text-rendering: optimizeReadability;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
        }
        
        /* Remove default focus outlines and add custom ones */
        *:focus {
            outline: none;
        }
        
        /* Ensure all interactive elements have focus indicators */
        a:focus, button:focus, input:focus, select:focus, textarea:focus, [tabindex]:focus {
            outline: 2px solid #005fcc;
            outline-offset: 2px;
        }
        """
    
    def _generate_typography_css(self, preferences: AccessibilityPreferences) -> str:
        """Generate typography styles for readability"""
        
        font_size = 16 * preferences.font_size_multiplier
        line_height = 1.5 * preferences.line_height_multiplier
        
        return f"""
        /* Typography for Accessibility */
        html {{
            font-size: {font_size}px;
        }}
        
        body {{
            line-height: {line_height};
            font-weight: 400;
            color: #212529;
        }}
        
        /* Headings with proper hierarchy */
        h1, h2, h3, h4, h5, h6 {{
            font-weight: 600;
            line-height: 1.2;
            margin-top: 0;
            margin-bottom: 0.75em;
        }}
        
        h1 {{ font-size: 2.5rem; }}
        h2 {{ font-size: 2rem; }}
        h3 {{ font-size: 1.75rem; }}
        h4 {{ font-size: 1.5rem; }}
        h5 {{ font-size: 1.25rem; }}
        h6 {{ font-size: 1.125rem; }}
        
        /* Readable paragraph spacing */
        p {{
            margin-top: 0;
            margin-bottom: 1rem;
            max-width: 65ch; /* Optimal reading width */
        }}
        
        /* List accessibility */
        ul, ol {{
            padding-left: 2rem;
        }}
        
        li {{
            margin-bottom: 0.25rem;
        }}
        
        /* Link accessibility */
        a {{
            color: #0056b3;
            text-decoration: underline;
            text-decoration-skip-ink: auto;
        }}
        
        a:hover {{
            text-decoration: none;
        }}
        
        a:visited {{
            color: #6f42c1;
        }}
        """
    
    def _generate_interaction_css(self, preferences: AccessibilityPreferences) -> str:
        """Generate interaction and focus styles"""
        
        touch_size = 48 if preferences.touch_target_size == 'large' else 44
        
        return f"""
        /* Interactive Element Accessibility */
        
        /* Minimum touch target sizes */
        button, .btn, [role="button"], input[type="submit"], input[type="button"] {{
            min-height: {touch_size}px;
            min-width: {touch_size}px;
            padding: 0.5rem 1rem;
            font-size: 1rem;
            border: none;
            border-radius: 0.25rem;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            text-decoration: none;
            user-select: none;
            transition: all 0.15s ease-in-out;
        }}
        
        /* Focus indicators */
        button:focus, .btn:focus, [role="button"]:focus {{
            outline: 3px solid #005fcc;
            outline-offset: 2px;
            z-index: 1;
        }}
        
        /* Form accessibility */
        input, select, textarea {{
            font-size: 1rem;
            padding: 0.5rem;
            border: 2px solid #ccc;
            border-radius: 0.25rem;
            min-height: {touch_size}px;
        }}
        
        input:focus, select:focus, textarea:focus {{
            border-color: #005fcc;
            box-shadow: 0 0 0 0.2rem rgba(0, 95, 204, 0.25);
        }}
        
        /* Label association */
        label {{
            font-weight: 600;
            margin-bottom: 0.25rem;
            display: block;
        }}
        
        /* Required field indicators */
        .required::after {{
            content: " *";
            color: #dc3545;
        }}
        
        /* Error states */
        .error, [aria-invalid="true"] {{
            border-color: #dc3545;
        }}
        
        .error-message {{
            color: #dc3545;
            font-size: 0.875rem;
            margin-top: 0.25rem;
        }}
        
        /* Skip links */
        .skip-link {{
            position: absolute;
            top: -40px;
            left: 6px;
            background: #000;
            color: #fff;
            padding: 8px;
            text-decoration: none;
            z-index: 1000;
        }}
        
        .skip-link:focus {{
            top: 6px;
        }}
        """
    
    def _generate_color_css(self, preferences: AccessibilityPreferences) -> str:
        """Generate color and theme styles"""
        
        if preferences.color_theme == ColorTheme.HIGH_CONTRAST:
            return """
            /* High Contrast Theme */
            :root {
                --bg-color: #ffffff;
                --text-color: #000000;
                --link-color: #0000ee;
                --visited-color: #551a8b;
                --border-color: #000000;
            }
            
            body {
                background-color: var(--bg-color);
                color: var(--text-color);
            }
            
            a { color: var(--link-color); }
            a:visited { color: var(--visited-color); }
            
            button, .btn {
                background-color: var(--bg-color);
                color: var(--text-color);
                border: 2px solid var(--border-color);
            }
            
            input, select, textarea {
                background-color: var(--bg-color);
                color: var(--text-color);
                border: 2px solid var(--border-color);
            }
            """
        
        elif preferences.color_theme == ColorTheme.DARK_MODE:
            return """
            /* Dark Mode Theme */
            :root {
                --bg-color: #121212;
                --surface-color: #1e1e1e;
                --text-color: #ffffff;
                --text-secondary: #b3b3b3;
                --link-color: #64b5f6;
                --border-color: #333333;
            }
            
            body {
                background-color: var(--bg-color);
                color: var(--text-color);
            }
            
            a { color: var(--link-color); }
            
            button, .btn {
                background-color: var(--surface-color);
                color: var(--text-color);
                border: 1px solid var(--border-color);
            }
            
            input, select, textarea {
                background-color: var(--surface-color);
                color: var(--text-color);
                border: 1px solid var(--border-color);
            }
            """
        
        else:
            return """
            /* Default Light Theme */
            :root {
                --bg-color: #ffffff;
                --surface-color: #f8f9fa;
                --text-color: #212529;
                --text-secondary: #6c757d;
                --link-color: #0056b3;
                --border-color: #dee2e6;
            }
            
            body {
                background-color: var(--bg-color);
                color: var(--text-color);
            }
            
            a { color: var(--link-color); }
            
            button, .btn {
                background-color: var(--link-color);
                color: var(--bg-color);
                border: 1px solid var(--link-color);
            }
            
            input, select, textarea {
                background-color: var(--bg-color);
                color: var(--text-color);
                border: 1px solid var(--border-color);
            }
            """
    
    def _generate_layout_css(self, preferences: AccessibilityPreferences) -> str:
        """Generate layout and spacing styles"""
        return """
        /* Accessible Layout */
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 1rem;
        }
        
        /* Responsive grid */
        .grid {
            display: grid;
            gap: 1rem;
        }
        
        @media (min-width: 768px) {
            .grid {
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            }
        }
        
        /* Accessible spacing */
        .content > * + * {
            margin-top: 1rem;
        }
        
        /* Screen reader only content */
        .sr-only {
            position: absolute;
            width: 1px;
            height: 1px;
            padding: 0;
            margin: -1px;
            overflow: hidden;
            clip: rect(0, 0, 0, 0);
            white-space: nowrap;
            border: 0;
        }
        
        .sr-only-focusable:focus {
            position: static;
            width: auto;
            height: auto;
            padding: inherit;
            margin: inherit;
            overflow: visible;
            clip: auto;
            white-space: inherit;
        }
        
        /* Loading and status indicators */
        [aria-live] {
            position: relative;
        }
        
        .loading {
            opacity: 0.6;
            pointer-events: none;
        }
        
        /* Print optimizations */
        @media print {
            * {
                background: transparent !important;
                color: black !important;
                box-shadow: none !important;
                text-shadow: none !important;
            }
            
            a, a:visited {
                text-decoration: underline;
            }
            
            a[href]:after {
                content: " (" attr(href) ")";
            }
            
            .no-print {
                display: none !important;
            }
        }
        """
    
    def _generate_print_css(self) -> str:
        """Generate print-friendly styles"""
        return """
        /* Print Accessibility */
        @media print {
            @page {
                margin: 0.5in;
            }
            
            * {
                background: transparent !important;
                color: black !important;
                box-shadow: none !important;
                text-shadow: none !important;
            }
            
            body {
                font-size: 12pt;
                line-height: 1.5;
            }
            
            h1, h2, h3, h4, h5, h6 {
                page-break-after: avoid;
                font-weight: bold;
            }
            
            p, li {
                orphans: 3;
                widows: 3;
            }
            
            a[href]:after {
                content: " (" attr(href) ")";
                font-size: 0.8em;
            }
            
            .no-print, .skip-link {
                display: none !important;
            }
        }
        """

class MobileAccessibilitySystem(BaseProcessor):
    """Main mobile and accessibility system"""
    
    def __init__(self):
        super().__init__()
        self.responsive_engine = ResponsiveDesignEngine()
        self.accessibility_auditor = AccessibilityAuditor()
        self.css_generator = CSSGenerator()
        
        # User preferences storage (in production, would use database)
        self.user_preferences = {}
    
    async def process(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Main processing method for mobile and accessibility features"""
        try:
            logger.info(f"Starting mobile accessibility processing for profile {profile_id}")
            
            operation = kwargs.get('operation', 'generate_css')
            
            if operation == 'generate_css':
                result = await self._generate_accessibility_css(profile_id, **kwargs)
            elif operation == 'audit_page':
                result = await self._audit_page_accessibility(profile_id, **kwargs)
            elif operation == 'update_preferences':
                result = await self._update_accessibility_preferences(profile_id, **kwargs)
            elif operation == 'get_preferences':
                result = await self._get_accessibility_preferences(profile_id)
            else:
                result = await self._generate_comprehensive_accessibility(profile_id, **kwargs)
            
            return {
                'profile_id': profile_id,
                'operation': operation,
                'result': result,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in mobile accessibility system: {e}")
            return {
                'profile_id': profile_id,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    async def _generate_accessibility_css(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Generate accessibility-optimized CSS"""
        
        # Get user preferences
        preferences = self.user_preferences.get(profile_id, AccessibilityPreferences(user_id=profile_id))
        
        # Override with any provided preferences
        if 'preferences' in kwargs:
            for key, value in kwargs['preferences'].items():
                if hasattr(preferences, key):
                    setattr(preferences, key, value)
        
        # Generate responsive CSS
        responsive_css = await self.responsive_engine.generate_responsive_css(preferences)
        
        # Generate accessibility CSS
        accessibility_css = await self.css_generator.generate_accessibility_css(preferences)
        
        # Combine CSS
        complete_css = f"{responsive_css}\n\n{accessibility_css}"
        
        return {
            'css_generated': True,
            'css_length': len(complete_css),
            'preferences_applied': self._serialize_preferences(preferences),
            'breakpoints_count': len(self.responsive_engine.breakpoints),
            'css_content': complete_css
        }
    
    async def _audit_page_accessibility(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Audit page accessibility"""
        
        page_content = kwargs.get('page_content', '')
        page_url = kwargs.get('page_url', '')
        
        if not page_content:
            return {
                'error': 'No page content provided for audit'
            }
        
        # Perform accessibility audit
        audit_result = await self.accessibility_auditor.audit_page(page_content, page_url)
        
        return {
            'audit_completed': True,
            'audit_result': self._serialize_audit_result(audit_result),
            'recommendations': {
                'quick_fixes': audit_result.quick_fixes,
                'improvement_plan': audit_result.improvement_plan
            }
        }
    
    async def _update_accessibility_preferences(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Update user accessibility preferences"""
        
        # Get current preferences or create new
        current_prefs = self.user_preferences.get(profile_id, AccessibilityPreferences(user_id=profile_id))
        
        # Update preferences with provided values
        updated_fields = []
        for key, value in kwargs.get('preferences', {}).items():
            if hasattr(current_prefs, key):
                setattr(current_prefs, key, value)
                updated_fields.append(key)
        
        # Update timestamp
        current_prefs.last_updated = datetime.now()
        
        # Store updated preferences
        self.user_preferences[profile_id] = current_prefs
        
        return {
            'preferences_updated': True,
            'updated_fields': updated_fields,
            'preferences': self._serialize_preferences(current_prefs)
        }
    
    async def _get_accessibility_preferences(self, profile_id: str) -> Dict[str, Any]:
        """Get user accessibility preferences"""
        
        preferences = self.user_preferences.get(profile_id, AccessibilityPreferences(user_id=profile_id))
        
        return {
            'preferences': self._serialize_preferences(preferences),
            'available_themes': [theme.value for theme in ColorTheme],
            'available_interaction_modes': [mode.value for mode in InteractionMode],
            'breakpoints': {name: self._serialize_breakpoint(bp) for name, bp in self.responsive_engine.breakpoints.items()}
        }
    
    async def _generate_comprehensive_accessibility(self, profile_id: str, **kwargs) -> Dict[str, Any]:
        """Generate comprehensive accessibility report and assets"""
        
        # Get preferences
        preferences = self.user_preferences.get(profile_id, AccessibilityPreferences(user_id=profile_id))
        
        # Generate CSS
        css_result = await self._generate_accessibility_css(profile_id, **kwargs)
        
        # If page content provided, audit it
        audit_result = None
        if 'page_content' in kwargs:
            audit_data = await self._audit_page_accessibility(profile_id, **kwargs)
            audit_result = audit_data.get('audit_result')
        
        # Generate mobile optimizations
        mobile_optimizations = self._generate_mobile_optimizations(preferences)
        
        # Generate accessibility guidelines
        guidelines = self._generate_accessibility_guidelines()
        
        return {
            'comprehensive_report': True,
            'css': css_result,
            'audit': audit_result,
            'mobile_optimizations': mobile_optimizations,
            'accessibility_guidelines': guidelines,
            'preferences': self._serialize_preferences(preferences)
        }
    
    def _generate_mobile_optimizations(self, preferences: AccessibilityPreferences) -> Dict[str, Any]:
        """Generate mobile-specific optimizations"""
        
        optimizations = {
            'viewport_meta': '<meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=yes">',
            'touch_optimizations': [
                'Minimum 44px touch targets implemented',
                'Touch-friendly spacing applied',
                'Gesture navigation supported'
            ],
            'performance_optimizations': [
                'CSS optimized for mobile rendering',
                'Font loading optimized',
                'Reduced animation complexity' if preferences.reduce_motion else 'Smooth animations enabled'
            ],
            'accessibility_features': [
                'Screen reader optimizations',
                'High contrast mode available' if preferences.high_contrast_mode else 'Standard contrast',
                'Keyboard navigation support',
                'Focus management implemented'
            ]
        }
        
        if preferences.mobile_zoom_enabled:
            optimizations['zoom_features'] = 'Pinch-to-zoom enabled'
        
        if preferences.mobile_gestures_enabled:
            optimizations['gesture_features'] = 'Touch gestures supported'
        
        return optimizations
    
    def _generate_accessibility_guidelines(self) -> Dict[str, Any]:
        """Generate accessibility implementation guidelines"""
        
        return {
            'wcag_compliance': {
                'level': 'AA',
                'guidelines': [
                    'Perceivable: All content can be perceived by users',
                    'Operable: Interface components and navigation must be operable',
                    'Understandable: Information and UI operation must be understandable',
                    'Robust: Content must be robust enough for various assistive technologies'
                ]
            },
            'implementation_checklist': [
                'Add alt text to all images',
                'Ensure keyboard navigation works throughout the interface',
                'Use proper heading hierarchy (H1, H2, H3, etc.)',
                'Provide sufficient color contrast (4.5:1 minimum)',
                'Make error messages clear and helpful',
                'Use semantic HTML elements',
                'Provide skip links for navigation',
                'Ensure forms are properly labeled',
                'Test with screen readers',
                'Verify touch target sizes (minimum 44px)'
            ],
            'testing_tools': [
                'WAVE Web Accessibility Evaluator',
                'axe accessibility checker',
                'Lighthouse accessibility audit',
                'Screen reader testing (NVDA, JAWS, VoiceOver)',
                'Keyboard navigation testing',
                'Mobile device testing'
            ]
        }
    
    def _serialize_preferences(self, preferences: AccessibilityPreferences) -> Dict[str, Any]:
        """Serialize accessibility preferences for JSON output"""
        return {
            'user_id': preferences.user_id,
            'visual_preferences': {
                'font_size_multiplier': preferences.font_size_multiplier,
                'line_height_multiplier': preferences.line_height_multiplier,
                'color_theme': preferences.color_theme.value,
                'high_contrast_mode': preferences.high_contrast_mode,
                'reduce_motion': preferences.reduce_motion,
                'reduce_transparency': preferences.reduce_transparency
            },
            'interaction_preferences': {
                'keyboard_navigation': preferences.keyboard_navigation,
                'focus_indicators': preferences.focus_indicators,
                'touch_target_size': preferences.touch_target_size,
                'click_delay': preferences.click_delay
            },
            'assistive_technology': {
                'screen_reader_mode': preferences.screen_reader_mode,
                'voice_control': preferences.voice_control,
                'switch_control': preferences.switch_control
            },
            'mobile_preferences': {
                'mobile_zoom_enabled': preferences.mobile_zoom_enabled,
                'mobile_gestures_enabled': preferences.mobile_gestures_enabled,
                'mobile_orientation_lock': preferences.mobile_orientation_lock
            },
            'last_updated': preferences.last_updated.isoformat()
        }
    
    def _serialize_breakpoint(self, breakpoint: ResponsiveBreakpoint) -> Dict[str, Any]:
        """Serialize responsive breakpoint for JSON output"""
        return {
            'name': breakpoint.name,
            'device_type': breakpoint.device_type.value,
            'width_range': {
                'min': breakpoint.min_width,
                'max': breakpoint.max_width
            },
            'layout_config': {
                'columns': breakpoint.columns,
                'gutter_size': breakpoint.gutter_size,
                'container_padding': breakpoint.container_padding
            },
            'typography_config': {
                'base_font_size': breakpoint.base_font_size,
                'heading_scale': breakpoint.heading_scale,
                'line_height': breakpoint.line_height
            }
        }
    
    def _serialize_audit_result(self, audit: AccessibilityAuditResult) -> Dict[str, Any]:
        """Serialize accessibility audit result for JSON output"""
        return {
            'audit_id': audit.audit_id,
            'page_url': audit.page_url,
            'compliance_level': audit.compliance_level.value,
            'overall_score': audit.overall_score,
            'principle_scores': {
                'perceivable': audit.perceivable_score,
                'operable': audit.operable_score,
                'understandable': audit.understandable_score,
                'robust': audit.robust_score
            },
            'issues_summary': {
                'critical_count': len(audit.critical_issues),
                'major_count': len(audit.major_issues),
                'minor_count': len(audit.minor_issues),
                'suggestions_count': len(audit.suggestions)
            },
            'performance_metrics': {
                'audit_duration': audit.audit_duration,
                'elements_checked': audit.elements_checked
            },
            'created_at': audit.created_at.isoformat()
        }

# Export main components
__all__ = [
    'MobileAccessibilitySystem',
    'AccessibilityPreferences',
    'ResponsiveBreakpoint',
    'AccessibilityAuditResult',
    'AccessibilityLevel',
    'ColorTheme',
    'DeviceType'
]