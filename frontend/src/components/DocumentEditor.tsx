import { useEffect } from 'react';
import { EditorContent, useEditor } from '@tiptap/react';
import type { JSONContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import { TableKit } from '@tiptap/extension-table';

export function DocumentEditor({ content, valueKey, editable, onChange }: {
  content: JSONContent; valueKey: string; editable: boolean; onChange: (value: JSONContent) => void;
}) {
  const editor = useEditor({
    extensions: [StarterKit.configure({ link: false, codeBlock: false, blockquote: false, horizontalRule: false }), TableKit],
    content, editable, onUpdate: ({ editor }) => onChange(editor.getJSON()),
    editorProps: { attributes: { 'aria-label': 'Nội dung tài liệu', role: 'textbox', 'aria-multiline': 'true' } },
  });
  useEffect(() => { editor?.commands.setContent(content, { emitUpdate: false }); }, [editor, valueKey]);
  // Changing read-only state is not a content edit; do not mark the draft dirty.
  useEffect(() => { editor?.setEditable(editable, false); }, [editor, editable]);
  if (!editor) return null;
  return <div className="editor-shell">
    <div className="toolbar" role="toolbar" aria-label="Định dạng tài liệu">
      <button disabled={!editable} aria-pressed={editor.isActive('bold')} onClick={() => editor.chain().focus().toggleBold().run()}><b>B</b></button>
      <button disabled={!editable} aria-pressed={editor.isActive('italic')} onClick={() => editor.chain().focus().toggleItalic().run()}><i>I</i></button>
      <button disabled={!editable} onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}>Tiêu đề</button>
      <button disabled={!editable} onClick={() => editor.chain().focus().toggleBulletList().run()}>• Danh sách</button>
      <button disabled={!editable} onClick={() => editor.chain().focus().toggleOrderedList().run()}>1. Đánh số</button>
      <button disabled={!editable} onClick={() => editor.chain().focus().insertTable({ rows: 3, cols: 2, withHeaderRow: true }).run()}>Chèn bảng</button>
      <button disabled={!editable || !editor.can().undo()} onClick={() => editor.chain().focus().undo().run()}>Hoàn tác</button>
    </div>
    <EditorContent editor={editor} />
  </div>;
}
