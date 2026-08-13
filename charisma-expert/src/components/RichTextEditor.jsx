import { useEffect } from 'react'
import { EditorContent, useEditor } from '@tiptap/react'
import StarterKit from '@tiptap/starter-kit'
import Link from '@tiptap/extension-link'
import Image from '@tiptap/extension-image'
import Underline from '@tiptap/extension-underline'
import TextAlign from '@tiptap/extension-text-align'
import Placeholder from '@tiptap/extension-placeholder'
import CharacterCount from '@tiptap/extension-character-count'
import {
  AlignCenter, AlignLeft, AlignRight, Bold, Code2, Eraser, Italic,
  Link as LinkIcon, List, ListOrdered, Minus, Quote, Redo2,
  Strikethrough, Underline as UnderlineIcon, Undo2, Image as ImageIcon,
} from 'lucide-react'

const ToolButton = ({ label, active = false, disabled = false, onClick, children }) => (
  <button type="button" aria-label={label} title={label} disabled={disabled}
    onMouseDown={(event) => event.preventDefault()} onClick={onClick}
    className={`p-2 rounded-md transition-colors disabled:opacity-30 disabled:cursor-not-allowed ${active ? 'bg-blue-100 text-blue-700' : 'text-gray-600 hover:text-gray-950 hover:bg-gray-100'}`}>
    {children}
  </button>
)

export default function RichTextEditor({ value, onChange, placeholder = 'Write your article…' }) {
  const editor = useEditor({
    extensions: [
      StarterKit.configure({ link: false, underline: false }),
      Link.configure({ openOnClick: false, autolink: true, defaultProtocol: 'https' }),
      Image.configure({ allowBase64: false, HTMLAttributes: { loading: 'lazy' } }),
      Underline,
      TextAlign.configure({ types: ['heading', 'paragraph'] }),
      Placeholder.configure({ placeholder }),
      CharacterCount,
    ],
    content: value || '',
    editorProps: {
      attributes: {
        class: 'blog-rich-content min-h-[360px] max-h-[55vh] overflow-y-auto px-5 py-4 outline-none',
        'aria-label': 'Article content',
      },
    },
    onUpdate: ({ editor: currentEditor }) => onChange(currentEditor.getHTML()),
  })

  useEffect(() => {
    if (!editor) return
    const nextValue = value || ''
    if (editor.getHTML() !== nextValue) editor.commands.setContent(nextValue, { emitUpdate: false })
  }, [editor, value])

  if (!editor) return <div className="h-[420px] rounded-xl border border-gray-300 bg-gray-50 animate-pulse" />

  const setLink = () => {
    const previous = editor.getAttributes('link').href || ''
    const url = window.prompt('Enter a link URL', previous)
    if (url === null) return
    if (!url.trim()) return editor.chain().focus().extendMarkRange('link').unsetLink().run()
    if (!/^https?:\/\//i.test(url) && !/^mailto:/i.test(url)) return
    editor.chain().focus().extendMarkRange('link').setLink({ href: url }).run()
  }

  const addImage = () => {
    const url = window.prompt('Enter a public https:// image URL')
    if (!url || !/^https:\/\//i.test(url)) return
    const alt = window.prompt('Describe the image for accessibility') || ''
    editor.chain().focus().setImage({ src: url, alt }).run()
  }

  const chain = () => editor.chain().focus()
  return (
    <div className="rounded-xl border border-gray-300 bg-white overflow-hidden focus-within:ring-2 focus-within:ring-blue-500 focus-within:border-blue-500">
      <div className="sticky top-0 z-10 flex flex-wrap items-center gap-0.5 px-2 py-1.5 border-b border-gray-200 bg-gray-50">
        <select aria-label="Text style" value={editor.isActive('heading', { level: 2 }) ? '2' : editor.isActive('heading', { level: 3 }) ? '3' : editor.isActive('heading', { level: 4 }) ? '4' : 'p'}
          onChange={(event) => event.target.value === 'p' ? chain().setParagraph().run() : chain().toggleHeading({ level: Number(event.target.value) }).run()}
          className="text-sm border-0 bg-transparent rounded-md py-1.5 pl-2 pr-7 text-gray-700 focus:ring-1 focus:ring-blue-500">
          <option value="p">Paragraph</option><option value="2">Heading 2</option><option value="3">Heading 3</option><option value="4">Heading 4</option>
        </select>
        <span className="w-px h-6 bg-gray-200 mx-1" />
        <ToolButton label="Bold" active={editor.isActive('bold')} onClick={() => chain().toggleBold().run()}><Bold size={17} /></ToolButton>
        <ToolButton label="Italic" active={editor.isActive('italic')} onClick={() => chain().toggleItalic().run()}><Italic size={17} /></ToolButton>
        <ToolButton label="Underline" active={editor.isActive('underline')} onClick={() => chain().toggleUnderline().run()}><UnderlineIcon size={17} /></ToolButton>
        <ToolButton label="Strikethrough" active={editor.isActive('strike')} onClick={() => chain().toggleStrike().run()}><Strikethrough size={17} /></ToolButton>
        <ToolButton label="Inline code" active={editor.isActive('code')} onClick={() => chain().toggleCode().run()}><Code2 size={17} /></ToolButton>
        <ToolButton label="Bulleted list" active={editor.isActive('bulletList')} onClick={() => chain().toggleBulletList().run()}><List size={17} /></ToolButton>
        <ToolButton label="Numbered list" active={editor.isActive('orderedList')} onClick={() => chain().toggleOrderedList().run()}><ListOrdered size={17} /></ToolButton>
        <ToolButton label="Quote" active={editor.isActive('blockquote')} onClick={() => chain().toggleBlockquote().run()}><Quote size={17} /></ToolButton>
        <ToolButton label="Link" active={editor.isActive('link')} onClick={setLink}><LinkIcon size={17} /></ToolButton>
        <ToolButton label="Image URL" onClick={addImage}><ImageIcon size={17} /></ToolButton>
        <ToolButton label="Divider" onClick={() => chain().setHorizontalRule().run()}><Minus size={17} /></ToolButton>
        <span className="w-px h-6 bg-gray-200 mx-1" />
        <ToolButton label="Align left" active={editor.isActive({ textAlign: 'left' })} onClick={() => chain().setTextAlign('left').run()}><AlignLeft size={17} /></ToolButton>
        <ToolButton label="Align center" active={editor.isActive({ textAlign: 'center' })} onClick={() => chain().setTextAlign('center').run()}><AlignCenter size={17} /></ToolButton>
        <ToolButton label="Align right" active={editor.isActive({ textAlign: 'right' })} onClick={() => chain().setTextAlign('right').run()}><AlignRight size={17} /></ToolButton>
        <ToolButton label="Clear formatting" onClick={() => chain().unsetAllMarks().clearNodes().run()}><Eraser size={17} /></ToolButton>
        <ToolButton label="Undo" disabled={!editor.can().chain().focus().undo().run()} onClick={() => chain().undo().run()}><Undo2 size={17} /></ToolButton>
        <ToolButton label="Redo" disabled={!editor.can().chain().focus().redo().run()} onClick={() => chain().redo().run()}><Redo2 size={17} /></ToolButton>
      </div>
      <EditorContent editor={editor} />
      <div className="px-4 py-2 border-t border-gray-100 bg-gray-50 text-right text-xs text-gray-500">
        {editor.storage.characterCount.characters().toLocaleString()} characters · {editor.storage.characterCount.words().toLocaleString()} words
      </div>
    </div>
  )
}
