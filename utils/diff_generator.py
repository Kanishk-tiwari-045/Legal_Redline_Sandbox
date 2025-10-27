import difflib
import html
from typing import Dict, List, Any

class DiffGenerator:
    """Generates HTML diffs between original and rewritten text"""
    
    def __init__(self):
        self.diff_styles = """
        <style>
        .diff-container {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
            border: 1px solid #ddd;
            border-radius: 5px;
            overflow: hidden;
        }
        .diff-header {
            background-color: #f8f9fa;
            padding: 10px;
            border-bottom: 1px solid #ddd;
            font-weight: bold;
        }
        .diff-content {
            max-height: 400px;
            overflow-y: auto;
        }
        table.diff {
            width: 100%;
            border-collapse: collapse;
            font-family: 'Courier New', monospace;
            font-size: 12px;
        }
        .diff td {
            padding: 2px 8px;
            vertical-align: top;
            white-space: pre-wrap;
            word-break: break-word;
        }
        .diff_header {
            background-color: #e9ecef;
            font-weight: bold;
            text-align: center;
            padding: 8px;
        }
        .diff_next {
            background-color: #007bff;
            color: white;
            text-align: center;
            padding: 4px;
            font-size: 10px;
        }
        .diff_add {
            background-color: #d4edda;
            border-left: 3px solid #28a745;
        }
        .diff_chg {
            background-color: #fff3cd;
            border-left: 3px solid #ffc107;
        }
        .diff_sub {
            background-color: #f8d7da;
            border-left: 3px solid #dc3545;
        }
        .diff_context {
            background-color: #f8f9fa;
        }
        .line-number {
            background-color: #e9ecef;
            color: #6c757d;
            text-align: right;
            padding-right: 8px;
            border-right: 1px solid #ddd;
            user-select: none;
            width: 40px;
        }
        </style>
        """
    
    def generate_html_diff(self, original: str, rewritten: str, context_lines: int = 3) -> str:
        """Generate an HTML diff between original and rewritten text"""
        
        # Split text into lines for better diff visualization
        original_lines = original.splitlines(keepends=True)
        rewritten_lines = rewritten.splitlines(keepends=True)
        
        # Create the diff
        differ = difflib.HtmlDiff(
            wrapcolumn=80,
            linejunk=difflib.IS_LINE_JUNK,
            charjunk=difflib.IS_CHARACTER_JUNK
        )
        
        diff_html = differ.make_table(
            original_lines,
            rewritten_lines,
            fromdesc="Original Clause",
            todesc="Rewritten Clause",
            context=True,
            numlines=context_lines
        )
        
        # Wrap with custom styling and container
        full_html = f"""
        {self.diff_styles}
        <div class="diff-container">
            <div class="diff-header">
                📊 Side-by-Side Comparison
            </div>
            <div class="diff-content">
                {diff_html}
            </div>
        </div>
        """
        
        return full_html
    
    def generate_unified_diff(self, original: str, rewritten: str, context_lines: int = 3) -> str:
        """Generate a unified diff format"""
        
        original_lines = original.splitlines(keepends=True)
        rewritten_lines = rewritten.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            rewritten_lines,
            fromfile='original_clause.txt',
            tofile='rewritten_clause.txt',
            n=context_lines
        )
        
        return ''.join(diff)
    
    def generate_inline_diff(self, original: str, rewritten: str) -> str:
        """Generate inline diff with highlighting"""
        
        # Use SequenceMatcher for character-level differences
        matcher = difflib.SequenceMatcher(None, original, rewritten)
        
        result_html = []
        
        for opcode, a1, a2, b1, b2 in matcher.get_opcodes():
            if opcode == 'equal':
                result_html.append(html.escape(original[a1:a2]))
            elif opcode == 'insert':
                result_html.append(f'<span class="diff-insert" style="background-color: #d4edda; color: #155724;">{html.escape(rewritten[b1:b2])}</span>')
            elif opcode == 'delete':
                result_html.append(f'<span class="diff-delete" style="background-color: #f8d7da; color: #721c24; text-decoration: line-through;">{html.escape(original[a1:a2])}</span>')
            elif opcode == 'replace':
                result_html.append(f'<span class="diff-delete" style="background-color: #f8d7da; color: #721c24; text-decoration: line-through;">{html.escape(original[a1:a2])}</span>')
                result_html.append(f'<span class="diff-insert" style="background-color: #d4edda; color: #155724;">{html.escape(rewritten[b1:b2])}</span>')
        
        return f'<div style="font-family: Arial, sans-serif; line-height: 1.6; padding: 15px; border: 1px solid #ddd; border-radius: 5px; background-color: #f8f9fa;">{"".join(result_html)}</div>'
    
    def generate_summary_diff(self, original: str, rewritten: str) -> Dict[str, Any]:
        """Generate a summary of changes made"""
        
        original_words = original.split()
        rewritten_words = rewritten.split()
        
        matcher = difflib.SequenceMatcher(None, original_words, rewritten_words)
        
        changes = {
            'additions': 0,
            'deletions': 0,
            'modifications': 0,
            'unchanged': 0,
            'similarity_ratio': matcher.ratio(),
            'word_count_change': len(rewritten_words) - len(original_words)
        }
        
        for opcode, a1, a2, b1, b2 in matcher.get_opcodes():
            if opcode == 'equal':
                changes['unchanged'] += (a2 - a1)
            elif opcode == 'insert':
                changes['additions'] += (b2 - b1)
            elif opcode == 'delete':
                changes['deletions'] += (a2 - a1)
            elif opcode == 'replace':
                changes['modifications'] += max((a2 - a1), (b2 - b1))
        
        # Calculate percentages
        total_original_words = len(original_words)
        if total_original_words > 0:
            changes['percent_changed'] = round(
                ((changes['additions'] + changes['deletions'] + changes['modifications']) 
                 / total_original_words) * 100, 2
            )
        else:
            changes['percent_changed'] = 0
        
        return changes
    
    def generate_change_highlights(self, original: str, rewritten: str) -> Dict[str, List[str]]:
        """Extract specific types of changes"""
        
        changes = {
            'added_phrases': [],
            'removed_phrases': [],
            'modified_phrases': []
        }
        
        # Split into sentences for better phrase detection
        original_sentences = [s.strip() for s in original.split('.') if s.strip()]
        rewritten_sentences = [s.strip() for s in rewritten.split('.') if s.strip()]
        
        matcher = difflib.SequenceMatcher(None, original_sentences, rewritten_sentences)
        
        for opcode, a1, a2, b1, b2 in matcher.get_opcodes():
            if opcode == 'insert':
                changes['added_phrases'].extend(rewritten_sentences[b1:b2])
            elif opcode == 'delete':
                changes['removed_phrases'].extend(original_sentences[a1:a2])
            elif opcode == 'replace':
                changes['modified_phrases'].extend([
                    f"Changed from: '{' '.join(original_sentences[a1:a2])}' to: '{' '.join(rewritten_sentences[b1:b2])}'"
                ])
        
        return changes
    
    def generate_structured_diff(self, original: str, rewritten: str) -> Dict[str, Any]:
        """Generate structured diff data for frontend display"""
        
        # Split into lines for processing
        original_lines = original.splitlines()
        rewritten_lines = rewritten.splitlines()
        
        # Create sequence matcher
        matcher = difflib.SequenceMatcher(None, original_lines, rewritten_lines)
        
        # Initialize results structure
        result = {
            'original_lines': [],
            'modified_lines': [],
            'unified_diff': [],
            'change_blocks': [],
            'stats': {
                'additions': 0,
                'deletions': 0,
                'modifications': 0,
                'total_changes': 0
            },
            'html_diff': self.generate_html_diff(original, rewritten)
        }
        
        original_line_num = 1
        modified_line_num = 1
        
        for opcode, a1, a2, b1, b2 in matcher.get_opcodes():
            if opcode == 'equal':
                # Context lines - same in both
                for i in range(a1, a2):
                    original_content = original_lines[i] if i < len(original_lines) else ''
                    result['original_lines'].append({
                        'line_number': original_line_num,
                        'content': original_content,
                        'type': 'context'
                    })
                    original_line_num += 1
                
                for i in range(b1, b2):
                    modified_content = rewritten_lines[i] if i < len(rewritten_lines) else ''
                    result['modified_lines'].append({
                        'line_number': modified_line_num,
                        'content': modified_content,
                        'type': 'context'
                    })
                    modified_line_num += 1
                    
                    # Add to unified diff too
                    result['unified_diff'].append({
                        'old_line_number': original_line_num - 1,
                        'new_line_number': modified_line_num - 1,
                        'content': modified_content,
                        'type': 'context',
                        'prefix': ' '
                    })
            
            elif opcode == 'delete':
                # Lines removed from original
                change_block = {
                    'type': 'deletion',
                    'original_lines': [],
                    'modified_lines': [],
                    'start_line': original_line_num
                }
                
                for i in range(a1, a2):
                    original_content = original_lines[i] if i < len(original_lines) else ''
                    result['original_lines'].append({
                        'line_number': original_line_num,
                        'content': original_content,
                        'type': 'removed'
                    })
                    change_block['original_lines'].append(original_content)
                    
                    # Add to unified diff
                    result['unified_diff'].append({
                        'old_line_number': original_line_num,
                        'new_line_number': None,
                        'content': original_content,
                        'type': 'removed',
                        'prefix': '-'
                    })
                    
                    original_line_num += 1
                    result['stats']['deletions'] += 1
                
                result['change_blocks'].append(change_block)
            
            elif opcode == 'insert':
                # Lines added to rewritten
                change_block = {
                    'type': 'addition',
                    'original_lines': [],
                    'modified_lines': [],
                    'start_line': modified_line_num
                }
                
                for i in range(b1, b2):
                    modified_content = rewritten_lines[i] if i < len(rewritten_lines) else ''
                    result['modified_lines'].append({
                        'line_number': modified_line_num,
                        'content': modified_content,
                        'type': 'added'
                    })
                    change_block['modified_lines'].append(modified_content)
                    
                    # Add to unified diff
                    result['unified_diff'].append({
                        'old_line_number': None,
                        'new_line_number': modified_line_num,
                        'content': modified_content,
                        'type': 'added',
                        'prefix': '+'
                    })
                    
                    modified_line_num += 1
                    result['stats']['additions'] += 1
                
                result['change_blocks'].append(change_block)
            
            elif opcode == 'replace':
                # Lines changed
                change_block = {
                    'type': 'modification',
                    'original_lines': [],
                    'modified_lines': [],
                    'start_line': original_line_num
                }
                
                # Process removed lines
                for i in range(a1, a2):
                    original_content = original_lines[i] if i < len(original_lines) else ''
                    result['original_lines'].append({
                        'line_number': original_line_num,
                        'content': original_content,
                        'type': 'removed'
                    })
                    change_block['original_lines'].append(original_content)
                    
                    result['unified_diff'].append({
                        'old_line_number': original_line_num,
                        'new_line_number': None,
                        'content': original_content,
                        'type': 'removed',
                        'prefix': '-'
                    })
                    
                    original_line_num += 1
                
                # Process added lines
                for i in range(b1, b2):
                    modified_content = rewritten_lines[i] if i < len(rewritten_lines) else ''
                    result['modified_lines'].append({
                        'line_number': modified_line_num,
                        'content': modified_content,
                        'type': 'added'
                    })
                    change_block['modified_lines'].append(modified_content)
                    
                    result['unified_diff'].append({
                        'old_line_number': None,
                        'new_line_number': modified_line_num,
                        'content': modified_content,
                        'type': 'added',
                        'prefix': '+'
                    })
                    
                    modified_line_num += 1
                
                result['stats']['modifications'] += max(a2 - a1, b2 - b1)
                result['change_blocks'].append(change_block)
        
        # Calculate total changes
        result['stats']['total_changes'] = (
            result['stats']['additions'] + 
            result['stats']['deletions'] + 
            result['stats']['modifications']
        )
        
        return result
