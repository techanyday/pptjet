from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR, PP_PARAGRAPH_ALIGNMENT, MSO_AUTO_SIZE
from pptx.dml.color import RGBColor
from pptx.enum.dml import MSO_THEME_COLOR
import os
import json
import openai
import requests
from typing import List, Dict, Optional

class PPTGenerator:
    def __init__(self):
        api_key = os.environ.get('OPENAI_API_KEY')
        print(f"Debug - API Key loaded in PPTGenerator: {api_key[:10]}...")
        if not api_key:
            raise ValueError("OpenAI API key not found in environment variables")
        try:
            self.client = openai.OpenAI(api_key=api_key)
            print("Debug - OpenAI client initialized successfully")
        except Exception as e:
            print(f"Debug - Error initializing OpenAI client: {str(e)}")
            raise
        
        # Define available template styles
        self.TEMPLATE_STYLES = {
            "Aesthetic": "Aesthetic.pptx",
            "Minimalist": "Minimalist.pptx",
            "Professional": "Professional.pptx",
            "Vintage": "Vintage.pptx"
        }
        
        # Define font settings (fallback for missing template styles)
        self.FONTS = {
            'title': {
                'name': 'Calibri',
                'size': Pt(44),
                'bold': True,
                'color': RGBColor(33, 33, 33)
            },
            'subtitle': {
                'name': 'Calibri',
                'size': Pt(32),
                'bold': False,
                'color': RGBColor(0, 123, 255)
            },
            'body': {
                'name': 'Calibri',
                'size': Pt(18),
                'bold': False,
                'color': RGBColor(33, 37, 41)
            }
        }

    def get_template_path(self, style: str) -> str:
        """Get the path to the selected template style"""
        filename = self.TEMPLATE_STYLES.get(style, "Professional.pptx")  # Default to Professional if style not found
        return os.path.join("app", "static", "presentations", "custom_styles", filename)

    def _remove_all_slides(self, prs: Presentation) -> None:
        """Remove all existing slides from the presentation while preserving the template"""
        xml_slides = prs.slides._sldIdLst
        slides = list(xml_slides)  # Create a list from iterator
        for slide_id in slides:
            xml_slides.remove(slide_id)

    def _apply_text_style(self, shape, style_type='body'):
        """Apply text style to a shape (only used if template styles are missing)"""
        if not shape.has_text_frame:
            return

        style = self.FONTS[style_type]
        text_frame = shape.text_frame
        text_frame.vertical_anchor = MSO_ANCHOR.MIDDLE
        
        for paragraph in text_frame.paragraphs:
            paragraph.font.name = style['name']
            paragraph.font.size = style['size']
            paragraph.font.bold = style['bold']
            paragraph.font.color.rgb = style['color']
            if style_type in ['title', 'subtitle']:
                paragraph.alignment = PP_ALIGN.CENTER

    def _get_layout_by_name(self, prs: Presentation, layout_name: str) -> Optional[any]:
        """Find a slide layout by its name"""
        for layout in prs.slide_layouts:
            if layout.name.lower() == layout_name.lower():
                return layout
        return None

    def _get_title_layout(self, prs: Presentation) -> any:
        """Get the title slide layout"""
        # Try to find a layout specifically for title slides
        layout = self._get_layout_by_name(prs, "Title Slide")
        if not layout:
            layout = self._get_layout_by_name(prs, "Title")
        if not layout:
            # Fallback to first layout which is typically the title layout
            layout = prs.slide_layouts[0]
        return layout

    def _get_content_layout(self, prs: Presentation) -> any:
        """Get the content slide layout"""
        # List of possible content layout names in order of preference
        layout_names = [
            "Title and Content",
            "TITLE_AND_BODY",      # Minimalist template
            "ONE_COLUMN_TEXT",    # Professional template
            "Content"
        ]
        
        # Try each layout name
        for name in layout_names:
            layout = self._get_layout_by_name(prs, name)
            if layout:
                print(f"Found content layout: {name}")
                return layout
        
        # If no named layout found, look for any layout with content placeholder
        for layout in prs.slide_layouts:
            for shape in layout.placeholders:
                if shape.placeholder_format.idx == 1:  # Content placeholder
                    print(f"Found layout with content placeholder: {layout.name}")
                    return layout
        
        # Final fallback to first non-title layout
        print("Warning: No content layout found, using fallback")
        return prs.slide_layouts[1] if len(prs.slide_layouts) > 1 else prs.slide_layouts[0]

    def _add_title_slide(self, prs: Presentation, title: str, presenter: str):
        """Add title slide"""
        layout = self._get_title_layout(prs)
        slide = prs.slides.add_slide(layout)
        
        # Add title if title placeholder exists
        if slide.shapes.title:
            slide.shapes.title.text = title
        
        # Add subtitle if subtitle placeholder exists
        subtitle = None
        for shape in slide.placeholders:
            if shape.placeholder_format.idx == 1:  # Subtitle placeholder
                subtitle = shape
                break
        
        if subtitle:
            subtitle.text = f"Presented by {presenter}"

    def _add_content_slide(self, prs: Presentation, title: str, content: str):
        """Add content slide"""
        layout = self._get_content_layout(prs)
        slide = prs.slides.add_slide(layout)
        
        # Add title if title placeholder exists
        if slide.shapes.title:
            slide.shapes.title.text = title
        
        # Find content placeholder
        content_placeholder = None
        for shape in slide.placeholders:
            if shape.placeholder_format.idx == 1:  # Content placeholder
                content_placeholder = shape
                break
        
        # Add content if placeholder exists
        if content_placeholder:
            text_frame = content_placeholder.text_frame
            text_frame.word_wrap = True
            
            # Add bullet points
            first = True
            for point in content.split('\n'):
                if first:
                    p = text_frame.paragraphs[0]
                    first = False
                else:
                    p = text_frame.add_paragraph()
                
                p.text = point.strip()
                p.level = 0
                p.space_before = Pt(12)
                p.space_after = Pt(12)
                p.line_spacing = 1.2

    def generate_slide_content(self, prompt: str, num_slides: int):
        """Generate slide content using GPT-3.5"""
        try:
            # First, generate a relevant title
            title_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a presentation title generator. Generate concise, professional titles."},
                    {"role": "user", "content": f"Generate a short, relevant title (max 5 words) for a presentation about: {prompt}. Return ONLY the title, nothing else."}
                ]
            )
            
            suggested_title = title_response.choices[0].message.content.strip().strip('"')
            
            # Then generate the slide content
            messages = [
                {
                    "role": "system",
                    "content": (
                        "You are a presentation content generator. Generate a JSON object with exactly this structure:\n"
                        "{\"slides\": [{\"title\": \"string\", \"content\": [\"string\"]}]}"
                        "\nThe 'slides' array MUST contain exactly the requested number of slides where:"
                        "\n- 'title' is the slide title"
                        "\n- 'content' is an array of 3-5 bullet points as strings"
                        "\nDo not include any explanation or other text, just the JSON."
                        "\nEnsure you generate exactly the requested number of unique slides."
                    )
                },
                {
                    "role": "user",
                    "content": f"Create exactly {num_slides} unique slides about: {prompt}. Each slide must have a unique title and 3-5 bullet points."
                }
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages
            )
        
            # Extract and parse the response
            response_text = response.choices[0].message.content
            print(f"Debug - OpenAI Response: {response_text}")
            response_data = json.loads(response_text)
            
            if not isinstance(response_data, dict) or 'slides' not in response_data:
                raise ValueError("Invalid response format from GPT. Expected object with 'slides' array.")
            
            slides_data = response_data['slides']
            print(f"Debug - Number of slides in response: {len(slides_data)}")
            
            if not isinstance(slides_data, list):
                raise ValueError("Invalid 'slides' format. Expected array.")
            
            # Ensure we have the right number of slides and format the content
            if len(slides_data) < num_slides:
                raise ValueError(f"OpenAI returned only {len(slides_data)} slides, but {num_slides} were requested")

            slides = []
            seen_titles = set()

            for slide in slides_data:
                if not isinstance(slide, dict) or 'title' not in slide or 'content' not in slide:
                    raise ValueError("Invalid slide format. Expected object with 'title' and 'content'.")
                
                if not isinstance(slide['content'], list):
                    raise ValueError("Invalid content format. Expected array of strings.")
                
                if slide['title'] in seen_titles:
                    continue  # Skip duplicate titles
                
                seen_titles.add(slide['title'])
                
                # Join content without bullet points - PowerPoint will add them automatically
                formatted_content = "\n".join(point.strip() for point in slide['content'])
                slides.append({
                    "title": slide['title'],
                    "content": formatted_content
                })
                print(f"Debug - Added slide: {slide['title']}")
                
                if len(slides) == num_slides:
                    break

            if len(slides) < num_slides:
                raise ValueError(f"Could not generate enough unique slides. Got {len(slides)}, needed {num_slides}")
                
            return {
                'suggested_title': suggested_title,
                'slides': slides
            }
        except json.JSONDecodeError as e:
            raise Exception(f"Error parsing GPT response: {str(e)}")
        except ValueError as e:
            raise Exception(f"Error in response format: {str(e)}")
        except Exception as e:
            raise Exception(f"Error generating content: {str(e)}")

    def create_presentation(self,
                        title: str,
                        presenter: str,
                        slides_content: List[Dict],
                        template: str = "Professional",
                        include_images: bool = False) -> str:
        """Create PowerPoint presentation using a selected template style"""
        # Load template
        template_path = self.get_template_path(template)
        try:
            prs = Presentation(template_path)
            # Remove any existing slides while preserving the template
            self._remove_all_slides(prs)
        except Exception as e:
            print(f"Warning: Could not load template {template_path}. Using blank presentation. Error: {str(e)}")
            prs = Presentation()

        # Add slides
        print(f"Debug - Adding title slide: {title}")
        self._add_title_slide(prs, title, presenter)
        
        print(f"Debug - Number of content slides to add: {len(slides_content)}")
        for slide_content in slides_content:
            # Add content slide first
            print(f"Debug - Adding content slide: {slide_content['title']}")
            self._add_content_slide(prs, slide_content['title'], slide_content['content'])



        # Get the absolute path to the generated directory
        generated_dir = os.path.abspath(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'generated'))
        
        # Ensure output directory exists
        os.makedirs(generated_dir, exist_ok=True)

        # Clean filename
        safe_title = "".join(c for c in title if c.isalnum() or c in (' ', '_')).rstrip()
        filename = f"{safe_title.replace(' ', '_')}.pptx"
        output_path = os.path.join(generated_dir, filename)

        prs.save(output_path)
        return output_path
