import markdown
from django import template
from django.utils.safestring import mark_safe
import re

register = template.Library()

@register.filter(name='markdown')
def markdown_format(text):
    """
    Convert markdown text to HTML with proper formatting
    """
    if not text:
        return ""
    
    # Configure markdown with extensions for better formatting
    md = markdown.Markdown(extensions=[
        'extra',      # Tables, fenced code blocks, etc.
        'nl2br',      # Convert newlines to <br> tags
        'sane_lists'  # Better list handling
    ])
    
    # Convert markdown to HTML
    html = md.convert(text)
    
    # Additional custom formatting for AI-generated content
    html = enhance_ai_formatting(html)
    
    return mark_safe(html)


@register.filter(name='smart_format')
def smart_format(text):
    """
    Smart formatting for AI-generated text that may not be pure markdown
    """
    if not text:
        return ""
    
    # First try markdown conversion
    html = markdown_format(text)
    
    # If markdown didn't find much to convert, apply manual formatting
    if html.count('<') < 3:  # Very few HTML tags, likely plain text
        html = manual_format_text(text)
    
    return mark_safe(html)


def enhance_ai_formatting(html):
    """
    Enhance HTML with additional formatting for AI-generated content
    """
    # Add custom CSS classes for better styling
    html = re.sub(r'<ul>', r'<ul class="ai-bullet-list">', html)
    html = re.sub(r'<ol>', r'<ol class="ai-numbered-list">', html)
    html = re.sub(r'<li>', r'<li class="ai-list-item">', html)
    html = re.sub(r'<h([1-6])', r'<h\1 class="ai-heading"', html)
    html = re.sub(r'<strong>', r'<strong class="ai-bold">', html)
    html = re.sub(r'<em>', r'<em class="ai-italic">', html)
    
    return html


def manual_format_text(text):
    """
    Manual formatting for text that doesn't follow strict markdown
    """
    lines = text.split('\n')
    formatted_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            formatted_lines.append('<br>')
            continue
        
        # Handle bullet points (*, -, •)
        if re.match(r'^[\*\-\•]\s+', line):
            if not in_list:
                formatted_lines.append('<ul class="ai-bullet-list">')
                in_list = True
            content = re.sub(r'^[\*\-\•]\s+', '', line)
            content = format_inline_text(content)
            formatted_lines.append(f'<li class="ai-list-item">{content}</li>')
        
        # Handle numbered lists
        elif re.match(r'^\d+[\.\)]\s+', line):
            if in_list:
                formatted_lines.append('</ul>')
            formatted_lines.append('<ol class="ai-numbered-list">')
            content = re.sub(r'^\d+[\.\)]\s+', '', line)
            content = format_inline_text(content)
            formatted_lines.append(f'<li class="ai-list-item">{content}</li>')
            formatted_lines.append('</ol>')
            in_list = False
        
        # Handle headings (lines that end with :)
        elif line.endswith(':') and len(line) < 100:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            content = format_inline_text(line[:-1])
            formatted_lines.append(f'<h4 class="ai-heading">{content}</h4>')
        
        # Regular paragraphs
        else:
            if in_list:
                formatted_lines.append('</ul>')
                in_list = False
            content = format_inline_text(line)
            formatted_lines.append(f'<p class="ai-paragraph">{content}</p>')
    
    # Close any open lists
    if in_list:
        formatted_lines.append('</ul>')
    
    return '\n'.join(formatted_lines)


def format_inline_text(text):
    """
    Format inline text elements like bold, italic, etc.
    """
    # Bold text (**text** or __text__)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong class="ai-bold">\1</strong>', text)
    text = re.sub(r'__(.*?)__', r'<strong class="ai-bold">\1</strong>', text)
    
    # Italic text (*text* or _text_)
    text = re.sub(r'\*(.*?)\*', r'<em class="ai-italic">\1</em>', text)
    text = re.sub(r'_(.*?)_', r'<em class="ai-italic">\1</em>', text)
    
    # Code text (`text`)
    text = re.sub(r'`(.*?)`', r'<code class="ai-code">\1</code>', text)
    
    return text


@register.filter(name='linebreaks_html')
def linebreaks_html(text):
    """
    Convert line breaks to HTML while preserving existing HTML
    """
    if not text:
        return ""
    
    # Split by HTML tags to avoid breaking them
    parts = re.split(r'(<[^>]+>)', text)
    result = []
    
    for part in parts:
        if part.startswith('<') and part.endswith('>'):
            # This is an HTML tag, keep as is
            result.append(part)
        else:
            # This is text, convert line breaks
            part = part.replace('\n\n', '</p><p class="ai-paragraph">')
            part = part.replace('\n', '<br>')
            if part and not part.startswith('<'):
                part = f'<p class="ai-paragraph">{part}</p>'
            result.append(part)
    
    return mark_safe(''.join(result))
