from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import Paragraph
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from io import BytesIO
from PIL import Image as PILImage
import re


def build_report(png_images_bytes, dataframe, output_path,
                 title="Report", page_size=letter,
                 images_per_row=1, max_image_width=6 * inch,
                 max_image_height=6 * inch, additional_info=None):
    """
    Create a PDF containing PNG images, a pandas DataFrame as a table, and additional markdown information.

    Parameters:
    -----------
    png_images_bytes : list
        List of PNG images as bytes objects
    dataframe : pandas.DataFrame
        DataFrame to be converted to a table in the PDF
    output_path : str
        Path where the PDF will be saved
    title : str, optional
        Title for the PDF document (default: "Report")
    page_size : tuple, optional
        Page size for the PDF (default: letter)
    images_per_row : int, optional
        Number of images to display per row (default: 1)
    max_image_width : float, optional
        Maximum width for images in points (default: 6 inches)
    max_image_height : float, optional
        Maximum height for images in points (default: 6 inches)
    additional_info : str, optional
        Markdown text to be included in the Additional Information section

    Returns:
    --------
    None
        Saves the PDF to the specified output_path

    Example:
    --------
    # Read some PNG files as bytes
    png_bytes = []
    for i in range(3):
        with open(f'image_{i}.png', 'rb') as f:
            png_bytes.append(f.read())

    # Create a sample DataFrame
    df = pd.DataFrame({
        'Feature': ['feature_1', 'feature_2', 'feature_3'],
        'Importance': [0.45, 0.32, 0.23],
        'Model': ['RandomForest', 'RandomForest', 'RandomForest']
    })

    # Additional information in markdown
    additional_text = '''
    ## Data Overview

    This analysis was performed on a dataset containing **1000 samples** with the following characteristics:

    - **Features**: 50 numeric features
    - **Target variable**: Binary classification (0/1)
    - **Missing values**: None after preprocessing

    ### Model Performance

    The Random Forest model achieved:
    - Accuracy: 92.5%
    - Precision: 91.2%
    - Recall: 93.8%

    **Note**: All metrics were calculated using 5-fold cross-validation.
    '''

    # Generate PDF
    build_report(png_bytes, df, 'output.pdf', additional_info=additional_text)
    """

    # Create the PDF document
    doc = SimpleDocTemplate(output_path, pagesize=page_size)
    story = []
    styles = getSampleStyleSheet()

    # Create custom styles for markdown rendering
    custom_styles = {
        'normal': ParagraphStyle(
            'CustomNormal',
            parent=styles['Normal'],
            fontSize=10,
            spaceAfter=6,
            alignment=TA_JUSTIFY
        ),
        'heading2': ParagraphStyle(
            'CustomHeading2',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6
        ),
        'heading3': ParagraphStyle(
            'CustomHeading3',
            parent=styles['Heading3'],
            fontSize=12,
            spaceBefore=10,
            spaceAfter=4
        ),
        'bullet': ParagraphStyle(
            'CustomBullet',
            parent=styles['Normal'],
            fontSize=10,
            leftIndent=20,
            bulletIndent=10,
            spaceAfter=3
        )
    }

    # Add title
    title_para = Paragraph(f"<b>{title}</b>", styles['Title'])
    story.append(title_para)
    story.append(Spacer(1, 12))

    # Process and add images
    if png_images_bytes:
        story.append(Paragraph("<b>Figures</b>", styles['Heading2']))
        story.append(Spacer(1, 6))

        # Group images into rows
        image_rows = []
        current_row = []

        for i, img_bytes in enumerate(png_images_bytes):
            try:
                # Create PIL Image to get dimensions
                pil_img = PILImage.open(BytesIO(img_bytes))
                img_width, img_height = pil_img.size

                # Calculate scaling to fit within max dimensions
                scale_w = max_image_width / img_width
                scale_h = max_image_height / img_height
                scale = min(scale_w, scale_h, 1.0)  # Don't upscale

                scaled_width = img_width * scale
                scaled_height = img_height * scale

                # Create ReportLab Image object
                img = Image(BytesIO(img_bytes), width=scaled_width, height=scaled_height)
                current_row.append(img)

                # If row is full or this is the last image, add row to story
                if len(current_row) == images_per_row or i == len(png_images_bytes) - 1:
                    if len(current_row) == 1:
                        # Single image, center it
                        story.append(img)
                    else:
                        # Multiple images, create a table to arrange them
                        img_table = Table([current_row])
                        img_table.setStyle(TableStyle([
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                        ]))
                        story.append(img_table)

                    story.append(Spacer(1, 12))
                    current_row = []

            except Exception as e:
                print(f"Warning: Could not process image {i}: {e}")
                continue

    # Add DataFrame as table
    if not dataframe.empty:
        story.append(Paragraph("<b>Feature Importance</b>", styles['Heading2']))
        story.append(Spacer(1, 6))

        # Prepare table data
        # Include column headers
        table_data = [list(dataframe.columns)]

        # Add data rows
        for _, row in dataframe.iterrows():
            table_data.append([f'{cell:.2f}' if isinstance(cell, float) else f'{cell}' for cell in row])

        # Create table
        table = Table(table_data)

        # Style the table
        table_style = TableStyle([
            # Header row styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),

            # Data rows styling
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),

            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

            # Alternating row colors for better readability
            *[('BACKGROUND', (0, i), (-1, i), colors.lightgrey)
              for i in range(2, len(table_data), 2)]
        ])

        table.setStyle(table_style)
        story.append(table)
        story.append(Spacer(1, 12))

    # Add Additional Information section
    if additional_info:
        story.append(Paragraph("<b>Additional Information</b>", styles['Heading2']))
        story.append(Spacer(1, 6))

        # Parse and render markdown-like content
        markdown_elements = parse_markdown_to_reportlab(additional_info, custom_styles)
        for element in markdown_elements:
            story.append(element)

    # Build the PDF
    doc.build(story)
    print(f"PDF created successfully: {output_path}")


def parse_markdown_to_reportlab(markdown_text, custom_styles):
    """
    Parse markdown text and convert it to ReportLab elements.

    Supported markdown features:
    - ## Heading 2
    - ### Heading 3
    - **bold text**
    - *italic text*
    - - bullet points
    - Regular paragraphs

    Parameters:
    -----------
    markdown_text : str
        Markdown formatted text
    custom_styles : dict
        Dictionary of custom paragraph styles

    Returns:
    --------
    list
        List of ReportLab elements (Paragraphs, Spacers)
    """
    elements = []
    lines = markdown_text.strip().split('\n')

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Skip empty lines
        if not line:
            i += 1
            continue

        # Heading 2 (##)
        if line.startswith('## '):
            heading_text = line[3:].strip()
            elements.append(Paragraph(f"<b>{heading_text}</b>", custom_styles['heading2']))

        # Heading 3 (###)
        elif line.startswith('### '):
            heading_text = line[4:].strip()
            elements.append(Paragraph(f"<b>{heading_text}</b>", custom_styles['heading3']))

        # Bullet point (-)
        elif line.startswith('- '):
            bullet_text = line[2:].strip()
            # Process inline formatting
            bullet_text = process_inline_formatting(bullet_text)
            elements.append(Paragraph(f"• {bullet_text}", custom_styles['bullet']))

        # Regular paragraph
        else:
            # Collect multi-line paragraphs
            paragraph_lines = [line]
            j = i + 1
            while j < len(lines) and lines[j].strip() and not lines[j].strip().startswith(('#', '-')):
                paragraph_lines.append(lines[j].strip())
                j += 1

            paragraph_text = ' '.join(paragraph_lines)
            if paragraph_text:
                # Process inline formatting
                paragraph_text = process_inline_formatting(paragraph_text)
                elements.append(Paragraph(paragraph_text, custom_styles['normal']))

            i = j - 1

        i += 1

    return elements


def process_inline_formatting(text):
    """
    Process inline markdown formatting like **bold** and *italic*.

    Parameters:
    -----------
    text : str
        Text with markdown formatting

    Returns:
    --------
    str
        Text with ReportLab XML formatting
    """
    # Convert **bold** to <b>bold</b>
    text = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # Convert *italic* to <i>italic</i> (but not already processed bold)
    text = re.sub(r'(?<!\*)\*([^*]+?)\*(?!\*)', r'<i>\1</i>', text)

    return text