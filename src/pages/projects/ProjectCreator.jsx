import { useState, useCallback, useEffect, useRef } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { motion } from 'framer-motion';
import { ArrowLeft, Save, Check, Loader2, Bold, Italic, Heading, List, Code2, Link2, Upload } from 'lucide-react';
import Button from '../../components/Button';
import Input from '../../components/Input';
import Card from '../../components/Card';
import MarkdownViewer from '../../components/MarkdownViewer';
import { useToast } from '../../context/ToastContext';
import { projectApi } from '../../services/api';
import './ProjectCreator.css';

const defaultSRS = `# Project SRS Document\n\n## Overview\nDescribe the project testing requirements here.\n\n## Test Scenarios\n1. **Scenario 1** — Description\n2. **Scenario 2** — Description\n\n## Acceptance Criteria\n- Criteria 1\n- Criteria 2\n`;

export default function ProjectCreator() {
  const { id } = useParams();
  const isEditing = !!id;
  
  const [name, setName] = useState('');
  const [url, setUrl] = useState('');
  const [markdown, setMarkdown] = useState(defaultSRS);
  const [loading, setLoading] = useState(isEditing);
  const [saving, setSaving] = useState(false);
  const [autoSaveStatus, setAutoSaveStatus] = useState('saved');
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();
  const toast = useToast();
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isEditing) {
      projectApi.getProject(id).then(data => {
        setName(data.name || '');
        setUrl(data.targetUrl || '');
        // For mock, just use defaultSRS if it doesn't have markdown
        setMarkdown(data.srsDocument || defaultSRS);
        setLoading(false);
      }).catch(() => {
        toast.error('Failed to load project');
        navigate('/projects');
      });
    }
  }, [id, isEditing, navigate, toast]);

  const validate = () => {
    const e = {};
    if (!name || name.length < 3) e.name = 'Project name must be at least 3 characters';
    if (!url || !/^https?:\/\/.+/.test(url)) e.url = 'Enter a valid URL (https://...)';
    setErrors(e);
    return Object.keys(e).length === 0;
  };

  const handleSave = async () => {
    if (!validate()) return;
    setSaving(true);
    try {
      if (isEditing) {
        await projectApi.updateProject(id, { name, targetUrl: url, srsDocument: markdown });
        toast.success('Project updated successfully!');
      } else {
        await projectApi.createProject({ name, targetUrl: url, srsDocument: markdown });
        toast.success('Project created successfully!');
      }
      navigate('/projects');
    } catch (err) {
      toast.error('Failed to save project');
    } finally {
      setSaving(false);
    }
  };

  const handleFileUpload = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      setMarkdown(event.target.result);
      setAutoSaveStatus('saving');
      setTimeout(() => setAutoSaveStatus('saved'), 1000);
      toast.success('File uploaded successfully');
    };
    reader.readAsText(file);
    e.target.value = null; // reset
  };

  const handleMarkdownChange = useCallback((e) => {
    setMarkdown(e.target.value);
    setAutoSaveStatus('saving');
    setTimeout(() => setAutoSaveStatus('saved'), 1000);
  }, []);

  const insertMarkdown = (syntax) => {
    setMarkdown(prev => prev + syntax);
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100%', flexDirection: 'column', gap: 16 }}>
        <Loader2 className="animate-spin" size={32} color="var(--primary)" />
        <p style={{ color: 'var(--text-secondary)' }}>Loading project details...</p>
      </div>
    );
  }

  return (
    <motion.div className="project-creator" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header">
        <div>
          <Button variant="ghost" size="sm" leftIcon={ArrowLeft} onClick={() => navigate('/projects')}>Back</Button>
          <h1 className="page-header__title" style={{ marginTop: 8 }}>{isEditing ? 'Edit Project' : 'Create New Project'}</h1>
          <p className="page-header__subtitle">{isEditing ? 'Update testing requirements' : 'Set up a new testing project with SRS document'}</p>
        </div>
        <div className="pc-autosave">
          {autoSaveStatus === 'saved' ? <><Check size={14} color="var(--success)" /> Saved</> : <><Loader2 size={14} className="animate-spin" /> Saving...</>}
        </div>
      </div>

      <Card className="pc-form">
        <h3 className="pc-section-title">Basic Information</h3>
        <div className="pc-fields">
          <Input label="Project Name" placeholder="E.g., E-Commerce Checkout Flow" value={name} onChange={e => setName(e.target.value)} error={errors.name} required />
          <Input label="Website URL" type="url" placeholder="https://your-website.com" value={url} onChange={e => setUrl(e.target.value)} error={errors.url} required />
        </div>

        <h3 className="pc-section-title" style={{ marginTop: 32 }}>SRS Document</h3>
        <div className="pc-editor-toolbar">
          <button className="pc-toolbar-btn" onClick={() => insertMarkdown('\n**bold**')} title="Bold"><Bold size={16} /></button>
          <button className="pc-toolbar-btn" onClick={() => insertMarkdown('\n*italic*')} title="Italic"><Italic size={16} /></button>
          <button className="pc-toolbar-btn" onClick={() => insertMarkdown('\n## Heading')} title="Heading"><Heading size={16} /></button>
          <button className="pc-toolbar-btn" onClick={() => insertMarkdown('\n- List item')} title="List"><List size={16} /></button>
          <button className="pc-toolbar-btn" onClick={() => insertMarkdown('\n`code`')} title="Code"><Code2 size={16} /></button>
          <button className="pc-toolbar-btn" onClick={() => insertMarkdown('\n[text](url)')} title="Link"><Link2 size={16} /></button>
          <div style={{ flex: 1 }} />
          <input type="file" ref={fileInputRef} onChange={handleFileUpload} accept=".txt,.md" style={{ display: 'none' }} />
          <Button variant="secondary" size="sm" leftIcon={Upload} onClick={() => fileInputRef.current?.click()}>Upload File</Button>
        </div>
        <div className="pc-editor">
          <div className="pc-editor__pane">
            <div className="pc-editor__label">Editor</div>
            <textarea className="pc-editor__textarea" value={markdown} onChange={handleMarkdownChange} spellCheck={false} />
          </div>
          <div className="pc-editor__divider" />
          <div className="pc-editor__pane">
            <div className="pc-editor__label">Preview</div>
            <div className="pc-editor__preview">
              <MarkdownViewer content={markdown} />
            </div>
          </div>
        </div>

        <div className="pc-actions">
          <Button variant="ghost" onClick={() => navigate('/projects')}>Cancel</Button>
          <Button variant="primary" leftIcon={Save} loading={saving} onClick={handleSave}>{isEditing ? 'Save Changes' : 'Save Project'}</Button>
        </div>
      </Card>
    </motion.div>
  );
}
