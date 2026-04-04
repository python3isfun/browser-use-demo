"""HTML to JSX conversion."""
import re
from bs4 import BeautifulSoup, NavigableString, Tag


class HTMLToJSXConverter:
    """Convert HTML to valid JSX with React-compatible attributes."""

    ATTRIBUTE_MAP = {
        # HTML attributes
        'class': 'className',
        'for': 'htmlFor',
        'tabindex': 'tabIndex',
        'readonly': 'readOnly',
        'maxlength': 'maxLength',
        'colspan': 'colSpan',
        'rowspan': 'rowSpan',
        'enctype': 'encType',
        'autocomplete': 'autoComplete',
        'autofocus': 'autoFocus',
        'autocorrect': 'autoCorrect',
        'autocapitalize': 'autoCapitalize',
        'contenteditable': 'contentEditable',
        'crossorigin': 'crossOrigin',
        'formaction': 'formAction',
        'formenctype': 'formEncType',
        'formmethod': 'formMethod',
        'formnovalidate': 'formNoValidate',
        'formtarget': 'formTarget',
        'hreflang': 'hrefLang',
        'inputmode': 'inputMode',
        'novalidate': 'noValidate',
        'srcdoc': 'srcDoc',
        'srcset': 'srcSet',
        'usemap': 'useMap',
        # SVG attributes
        'viewbox': 'viewBox',
        'preserveaspectratio': 'preserveAspectRatio',
        'attributename': 'attributeName',
        'attributetype': 'attributeType',
        'basefrequency': 'baseFrequency',
        'calcmode': 'calcMode',
        'clippathunits': 'clipPathUnits',
        'diffuseconstant': 'diffuseConstant',
        'edgemode': 'edgeMode',
        'filterunits': 'filterUnits',
        'glyphref': 'glyphRef',
        'gradienttransform': 'gradientTransform',
        'gradientunits': 'gradientUnits',
        'kernelmatrix': 'kernelMatrix',
        'kernelunitlength': 'kernelUnitLength',
        'keypoints': 'keyPoints',
        'keysplines': 'keySplines',
        'keytimes': 'keyTimes',
        'lengthadjust': 'lengthAdjust',
        'limitingconeangle': 'limitingConeAngle',
        'markerheight': 'markerHeight',
        'markerunits': 'markerUnits',
        'markerwidth': 'markerWidth',
        'maskcontentunits': 'maskContentUnits',
        'maskunits': 'maskUnits',
        'numoctaves': 'numOctaves',
        'pathlength': 'pathLength',
        'patterncontentunits': 'patternContentUnits',
        'patterntransform': 'patternTransform',
        'patternunits': 'patternUnits',
        'pointsatx': 'pointsAtX',
        'pointsaty': 'pointsAtY',
        'pointsatz': 'pointsAtZ',
        'primitiveunits': 'primitiveUnits',
        'refx': 'refX',
        'refy': 'refY',
        'repeatcount': 'repeatCount',
        'repeatdur': 'repeatDur',
        'requiredextensions': 'requiredExtensions',
        'requiredfeatures': 'requiredFeatures',
        'specularconstant': 'specularConstant',
        'specularexponent': 'specularExponent',
        'spreadmethod': 'spreadMethod',
        'startoffset': 'startOffset',
        'stddeviation': 'stdDeviation',
        'stitchtiles': 'stitchTiles',
        'surfacescale': 'surfaceScale',
        'systemlanguage': 'systemLanguage',
        'tablevalues': 'tableValues',
        'targetx': 'targetX',
        'targety': 'targetY',
        'textlength': 'textLength',
        'xchannelselector': 'xChannelSelector',
        'ychannelselector': 'yChannelSelector',
        'zoomandpan': 'zoomAndPan',
        # SVG hyphenated attributes
        'stroke-width': 'strokeWidth',
        'stroke-linecap': 'strokeLinecap',
        'stroke-linejoin': 'strokeLinejoin',
        'stroke-dasharray': 'strokeDasharray',
        'stroke-dashoffset': 'strokeDashoffset',
        'stroke-miterlimit': 'strokeMiterlimit',
        'stroke-opacity': 'strokeOpacity',
        'fill-opacity': 'fillOpacity',
        'fill-rule': 'fillRule',
        'clip-path': 'clipPath',
        'clip-rule': 'clipRule',
        'font-family': 'fontFamily',
        'font-size': 'fontSize',
        'font-style': 'fontStyle',
        'font-weight': 'fontWeight',
        'text-anchor': 'textAnchor',
        'text-decoration': 'textDecoration',
        'dominant-baseline': 'dominantBaseline',
        'alignment-baseline': 'alignmentBaseline',
        'baseline-shift': 'baselineShift',
        'stop-color': 'stopColor',
        'stop-opacity': 'stopOpacity',
        'color-interpolation': 'colorInterpolation',
        'color-interpolation-filters': 'colorInterpolationFilters',
        'flood-color': 'floodColor',
        'flood-opacity': 'floodOpacity',
        'lighting-color': 'lightingColor',
    }

    SELF_CLOSING_TAGS = {
        'area', 'base', 'br', 'col', 'embed', 'hr', 'img',
        'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'
    }

    SKIP_TAGS = {'script', 'style', 'noscript', 'head', 'html'}

    def __init__(self, mode: str = 'shallow'):
        """Initialize converter with mode ('full' or 'shallow')."""
        self.mode = mode

    def convert(self, html: str, styles_map: dict = None, assets_map: dict = None) -> str:
        """Convert HTML string to JSX string."""
        # Use html.parser instead of lxml - lxml incorrectly nests void elements
        # like <source> which breaks <picture> elements
        soup = BeautifulSoup(html, 'html.parser')
        body = soup.find('body')

        if not body:
            return '<div>Failed to parse page</div>'

        jsx = self._convert_element(body, styles_map or {}, assets_map or {})
        return jsx

    def _convert_element(self, element, styles_map: dict, assets_map: dict, indent: int = 0) -> str:
        """Recursively convert an element to JSX."""
        if isinstance(element, NavigableString):
            text = str(element)
            # Preserve whitespace but trim excessive newlines
            if text.strip():
                return self._escape_jsx_text(text)
            elif '\n' in text:
                return '\n'
            return ''

        if not isinstance(element, Tag):
            return ''

        tag_name = element.name

        # Skip unwanted tags
        if tag_name in self.SKIP_TAGS:
            return ''

        # Handle body tag specially - just process children
        if tag_name == 'body':
            children_jsx = self._process_children(element, styles_map, assets_map, indent)
            return children_jsx

        # Convert attributes
        attrs = self._convert_attributes(element, styles_map, assets_map)
        attrs_str = self._attrs_to_string(attrs)

        # Handle self-closing tags
        if tag_name in self.SELF_CLOSING_TAGS:
            return f'<{tag_name}{attrs_str} />'

        # Process children
        children_jsx = self._process_children(element, styles_map, assets_map, indent + 2)

        if children_jsx.strip():
            return f'<{tag_name}{attrs_str}>{children_jsx}</{tag_name}>'
        return f'<{tag_name}{attrs_str}></{tag_name}>'

    def _process_children(self, element: Tag, styles_map: dict, assets_map: dict, indent: int) -> str:
        """Process all children of an element."""
        children = []
        for child in element.children:
            child_jsx = self._convert_element(child, styles_map, assets_map, indent)
            if child_jsx:
                children.append(child_jsx)
        return ''.join(children)

    def _convert_attributes(self, element: Tag, styles_map: dict, assets_map: dict) -> dict:
        """Convert HTML attributes to JSX attributes."""
        result = {}

        for attr, value in element.attrs.items():
            # Skip data-clone-id, we'll use it but not output it
            if attr == 'data-clone-id':
                continue

            # Handle class -> className
            jsx_attr = self.ATTRIBUTE_MAP.get(attr, attr)

            if attr == 'class':
                if isinstance(value, list):
                    value = ' '.join(value)
                result['className'] = self._format_attr_value(value)

            elif attr == 'style':
                # Parse and convert inline style
                style_obj = self._parse_inline_style(value)
                if style_obj:
                    result['style'] = self._style_to_jsx(style_obj)

            elif attr.startswith('data-') and attr != 'data-clone-id':
                # Use JSX expression for data attributes (may contain JSON)
                result[attr] = '{' + f'"{self._escape_js_string(str(value))}"' + '}'

            elif attr in ('disabled', 'checked', 'selected', 'readonly', 'required', 'multiple', 'hidden'):
                if value or value == '':
                    result[jsx_attr] = '{true}'

            elif attr == 'src':
                # Replace asset URLs with local paths
                new_value = assets_map.get(value, value)
                result['src'] = self._format_attr_value(new_value)

            elif attr == 'srcset':
                # Replace URLs in srcset (format: "url1 1x, url2 2x, url3 300w")
                new_srcset = self._rewrite_srcset(value, assets_map)
                result['srcSet'] = self._format_attr_value(new_srcset)

            elif attr == 'data-srcset':
                # Replace URLs in data-srcset (lazy loading)
                new_srcset = self._rewrite_srcset(value, assets_map)
                result['data-srcset'] = '{' + f'"{self._escape_js_string(new_srcset)}"' + '}'

            elif attr == 'data-src':
                # Replace lazy-loaded src
                new_value = assets_map.get(value, value)
                result['data-src'] = '{' + f'"{self._escape_js_string(new_value)}"' + '}'

            elif attr == 'poster':
                # Video poster image
                new_value = assets_map.get(value, value)
                result['poster'] = self._format_attr_value(new_value)

            elif attr == 'href':
                result['href'] = self._format_attr_value(value)
                # Add mock handler for links - escape for JS string
                js_escaped = self._escape_js_string(value)
                result['onClick'] = '{(e) => { e.preventDefault(); console.log("[Mock] Navigate:", "' + js_escaped + '"); }}'

            elif attr in ('onclick', 'onsubmit', 'onchange', 'oninput'):
                # Skip inline event handlers, we'll add mock ones
                continue

            else:
                if isinstance(value, list):
                    value = ' '.join(value)
                result[jsx_attr] = self._format_attr_value(value)

        # Add computed styles from data-clone-id (shallow mode only)
        if self.mode == 'shallow':
            clone_id = element.get('data-clone-id')
            if clone_id and clone_id in styles_map:
                computed = styles_map[clone_id]
                if 'style' in result:
                    # Merge with existing inline styles
                    existing = self._parse_jsx_style(result['style'])
                    existing.update(computed)
                    result['style'] = self._style_to_jsx(existing)
                else:
                    result['style'] = self._style_to_jsx(computed)

        # Add mock handlers for interactive elements
        tag_name = element.name
        if tag_name == 'button':
            result['onClick'] = '{(e) => { e.preventDefault(); console.log("[Mock] Button clicked"); }}'
        elif tag_name == 'form':
            result['onSubmit'] = '{(e) => { e.preventDefault(); console.log("[Mock] Form submitted"); alert("Form submission mocked!"); }}'
        elif tag_name == 'input':
            input_type = element.get('type', 'text')
            if input_type not in ('submit', 'button', 'reset'):
                result['onChange'] = '{(e) => console.log("[Mock] Input changed:", e.target.value)}'

        return result

    def _attrs_to_string(self, attrs: dict) -> str:
        """Convert attributes dict to JSX string."""
        if not attrs:
            return ''
        parts = [f'{key}={value}' for key, value in attrs.items()]
        return ' ' + ' '.join(parts)

    def _parse_inline_style(self, style_str: str) -> dict:
        """Parse CSS inline style string to dict."""
        if not style_str:
            return {}
        result = {}
        for item in style_str.split(';'):
            if ':' in item:
                prop, value = item.split(':', 1)
                result[prop.strip()] = value.strip()
        return result

    def _parse_jsx_style(self, jsx_style: str) -> dict:
        """Parse JSX style object string back to dict."""
        # This is a simplified parser for our own output
        # Format: {{ prop: "value", prop2: "value2" }}
        result = {}
        content = jsx_style.strip('{}').strip()
        if not content:
            return result
        # Use regex to extract key-value pairs
        pattern = r'(\w+):\s*"([^"]*)"'
        matches = re.findall(pattern, content)
        for key, value in matches:
            # Convert camelCase back to kebab-case
            kebab_key = re.sub(r'([A-Z])', r'-\1', key).lower()
            result[kebab_key] = value
        return result

    def _style_to_jsx(self, style_dict: dict) -> str:
        """Convert style dict to JSX style object string."""
        jsx_styles = {}
        for prop, value in style_dict.items():
            camel_prop = self._to_camel_case(prop)
            # Escape quotes and backslashes in style values
            escaped_value = self._escape_attr_value(value)
            jsx_styles[camel_prop] = escaped_value
        if not jsx_styles:
            return '{{}}'
        items = ', '.join(f'{k}: "{v}"' for k, v in jsx_styles.items())
        return '{{' + items + '}}'

    def _to_camel_case(self, kebab: str) -> str:
        """Convert kebab-case to camelCase."""
        parts = kebab.split('-')
        return parts[0] + ''.join(p.capitalize() for p in parts[1:])

    def _escape_jsx_text(self, text: str) -> str:
        """Escape special characters in JSX text content."""
        text = text.replace('{', '&#123;')
        text = text.replace('}', '&#125;')
        text = text.replace('<', '&lt;')
        text = text.replace('>', '&gt;')
        return text

    def _escape_attr_value(self, value: str) -> str:
        """Escape special characters in JSX attribute values."""
        if not isinstance(value, str):
            value = str(value)
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        return value

    def _escape_js_string(self, value: str) -> str:
        """Escape special characters for JavaScript string literals."""
        if not isinstance(value, str):
            value = str(value)
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        value = value.replace('\n', '\\n')
        value = value.replace('\r', '\\r')
        return value

    def _format_attr_value(self, value: str) -> str:
        """Format attribute value for JSX, using expression syntax if needed."""
        if not isinstance(value, str):
            value = str(value)
        # Use JSX expression for values with quotes or special chars
        if '"' in value or '\\' in value or '\n' in value:
            return '{' + f'"{self._escape_js_string(value)}"' + '}'
        # Simple values can use quoted syntax
        return f'"{value}"'

    def _rewrite_srcset(self, srcset: str, assets_map: dict) -> str:
        """Rewrite URLs in srcset attribute to local paths."""
        if not srcset:
            return srcset
        entries = []
        for entry in srcset.split(','):
            entry = entry.strip()
            if not entry:
                continue
            parts = entry.split()
            if parts:
                url = parts[0]
                descriptor = ' '.join(parts[1:]) if len(parts) > 1 else ''
                # Replace URL with local path if available
                new_url = assets_map.get(url, url)
                if descriptor:
                    entries.append(f'{new_url} {descriptor}')
                else:
                    entries.append(new_url)
        return ', '.join(entries)
