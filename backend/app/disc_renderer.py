"""Locked-down proof-of-concept renderer for original eLearn XML."""

from __future__ import annotations

import html
import gzip
import re
import xml.etree.ElementTree as ET


FORBIDDEN_DECLARATIONS = re.compile(r"<!\s*(?:DOCTYPE|ENTITY)", re.IGNORECASE)
FORBIDDEN_TAGS = {"script", "object", "embed", "applet", "iframe", "activex", "vbscript"}
FORBIDDEN_SVG_TAGS = FORBIDDEN_TAGS | {"foreignobject", "audio", "video"}
HEADING_TAGS = {"bigtext1": "h2", "bigtext2": "h3", "title": "h2", "subtitle": "h3"}
BLOCK_TAGS = {"text": "p", "note": "aside", "warning": "aside", "description": "p"}
IMAGE_TAGS = {"jpgimage": "imageid", "svgimage": "imageid", "consvgimage": "conimageid"}


class UnsafeXmlError(ValueError):
    pass


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower()


def _plain_text(node: ET.Element) -> str:
    return " ".join(part.strip() for part in node.itertext() if part and part.strip())


def _first_text(node: ET.Element, name: str) -> str:
    for child in node.iter():
        if _local_name(child.tag) == name:
            return _plain_text(child)
    return ""


def parse_safe_xml(raw_xml: str) -> ET.Element:
    if FORBIDDEN_DECLARATIONS.search(raw_xml or ""):
        raise UnsafeXmlError("DTD and entity declarations are forbidden")
    try:
        root = ET.fromstring(raw_xml or "<group />")
    except ET.ParseError as exc:
        raise UnsafeXmlError(f"invalid XML: {exc}") from exc
    for node in root.iter():
        if _local_name(node.tag) in FORBIDDEN_TAGS:
            raise UnsafeXmlError(f"forbidden element: {_local_name(node.tag)}")
    return root


def render_xml(raw_xml: str) -> str:
    """Render source XML without XSLT, file access, network access, or active content."""
    root = parse_safe_xml(raw_xml)

    def render(node: ET.Element) -> str:
        name = _local_name(node.tag)
        if name == "link":
            target = _first_text(node, "targetid")
            code = _first_text(node, "code")
            link_text = _first_text(node, "text")
            description = _first_text(node, "description")
            label_parts = []
            for part in (link_text, code, description):
                if part and part not in label_parts:
                    label_parts.append(part)
            label = " ".join(label_parts) or f"Target {target}"
            safe_target = target if target.isdigit() else "unresolved"
            return (
                f'<a class="disc-link" href="disc://element/{safe_target}" '
                f'data-targetid="{html.escape(target, quote=True)}" '
                f'data-code="{html.escape(code, quote=True)}">{html.escape(label)}</a>'
            )
        reference_kind = IMAGE_TAGS.get(name)
        if not reference_kind:
            for child in list(node):
                child_name = _local_name(child.tag)
                if child_name in {"imageid", "conimageid"}:
                    reference_kind = child_name
                    break
        if reference_kind:
            asset_id = _first_text(node, reference_kind)
            if not asset_id:
                return ""
            return (
                f'<img class="disc-asset" src="disc-asset://{html.escape(asset_id, quote=True)}" '
                f'data-asset-id="{html.escape(asset_id, quote=True)}" '
                f'data-reference-kind="{reference_kind}" alt="" />'
            )
        children = "".join(
            render(child) + html.escape((child.tail or "").strip()) for child in list(node)
        )
        direct = html.escape((node.text or "").strip())
        content = direct + children
        if name in HEADING_TAGS:
            tag = HEADING_TAGS[name]
            return f"<{tag}>{content}</{tag}>"
        if name in BLOCK_TAGS:
            tag = BLOCK_TAGS[name]
            return f'<{tag} class="source-{name}">{content}</{tag}>'
        if name in {"table", "tbody", "thead", "tr", "td", "th", "ul", "ol", "li"}:
            return f"<{name}>{content}</{name}>"
        if name in {"group", "chapter", "section"}:
            return f'<section class="source-{name}">{content}</section>'
        return content

    return '<article class="disc-content">' + render(root) + "</article>"


def sanitize_svg_bytes(data: bytes, compressed: bool = False) -> bytes:
    """Return inert SVG bytes, rejecting active or externally loaded content."""
    if compressed:
        try:
            data = gzip.decompress(data)
        except (OSError, EOFError) as exc:
            raise UnsafeXmlError("invalid gzipped SVG") from exc
    if len(data) > 16 * 1024 * 1024:
        raise UnsafeXmlError("SVG exceeds the preview size limit")
    try:
        source = data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            source = data.decode("windows-1252")
        except UnicodeDecodeError as exc:
            raise UnsafeXmlError("SVG is not valid text") from exc
    root = parse_safe_xml(source)
    if _local_name(root.tag) != "svg":
        raise UnsafeXmlError("asset is not an SVG document")
    for node in root.iter():
        if _local_name(node.tag) in FORBIDDEN_SVG_TAGS:
            raise UnsafeXmlError(f"forbidden SVG element: {_local_name(node.tag)}")
        for name, value in list(node.attrib.items()):
            local = _local_name(name)
            value_lower = value.strip().lower()
            if local.startswith("on") or "url(" in value_lower:
                del node.attrib[name]
            elif local in {"href", "src"} and not value_lower.startswith("#"):
                del node.attrib[name]
    return ET.tostring(root, encoding="utf-8", xml_declaration=True)
