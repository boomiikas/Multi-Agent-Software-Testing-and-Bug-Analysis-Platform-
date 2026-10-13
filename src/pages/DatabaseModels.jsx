import { motion } from 'framer-motion';
import { Database, Check, X, ArrowRight, Key, Hash } from 'lucide-react';
import Card from '../components/Card';
import Badge from '../components/Badge';
import { databaseModels } from '../data/mockData';
import './DatabaseModels.css';

const typeColors = { ObjectId: 'primary', String: 'success', Number: 'warning', Date: 'info', Boolean: 'danger', '[Object]': 'primary', '[String]': 'default', Object: 'default' };

export default function DatabaseModels() {
  const models = Object.values(databaseModels);

  return (
    <motion.div className="db-page" initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
      <div className="page-header"><div><h1 className="page-header__title"><Database size={24} /> Database Models</h1><p className="page-header__subtitle">MongoDB schema documentation</p></div></div>

      <div className="db-relationship">
        <div className="db-rel-node">User</div>
        <ArrowRight size={20} className="db-rel-arrow" />
        <div className="db-rel-node">Project</div>
        <ArrowRight size={20} className="db-rel-arrow" />
        <div className="db-rel-node">TestRun</div>
      </div>

      <div className="db-models">
        {models.map((model, idx) => (
          <motion.div key={model.name} initial={{ opacity: 0, y: 16 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: idx * 0.1 }}>
            <Card padding="none" className="db-card">
              <div className="db-card__header">
                <h3><Database size={18} /> {model.name}</h3>
                <code className="db-card__collection">{model.collection}</code>
              </div>
              <table className="db-table">
                <thead><tr><th>Field</th><th>Type</th><th>Required</th><th>Default</th><th>Description</th></tr></thead>
                <tbody>
                  {model.fields.map(f => (
                    <tr key={f.name}>
                      <td>
                        <code className="db-field-name">{f.name}</code>
                        {f.unique && <Badge variant="info" size="sm" style={{ marginLeft: 4 }}>unique</Badge>}
                        {f.index && <Badge variant="default" size="sm" style={{ marginLeft: 4 }}><Hash size={10} />index</Badge>}
                        {f.ref && <Badge variant="warning" size="sm" style={{ marginLeft: 4 }}><ArrowRight size={10} />{f.ref}</Badge>}
                      </td>
                      <td><Badge variant={typeColors[f.type] || 'default'} size="sm">{f.type}</Badge></td>
                      <td>{f.required ? <Check size={14} color="var(--success)" /> : <X size={14} color="var(--text-muted)" />}</td>
                      <td><code className="db-default">{f.default || '—'}</code></td>
                      <td className="db-desc">{f.description}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {model.fields.some(f => f.enum) && (
                <div className="db-enums">
                  {model.fields.filter(f => f.enum).map(f => (
                    <div key={f.name} className="db-enum"><span className="db-enum__label">{f.name}:</span> {f.enum.map(v => <Badge key={v} variant="default" size="sm">{v}</Badge>)}</div>
                  ))}
                </div>
              )}
            </Card>
          </motion.div>
        ))}
      </div>
    </motion.div>
  );
}
