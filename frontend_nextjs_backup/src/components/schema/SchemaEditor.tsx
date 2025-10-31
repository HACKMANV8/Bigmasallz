'use client';

import { useState } from 'react';
import type { DataSchema } from '@/types/schema';

interface SchemaEditorProps {
  schema: DataSchema;
  onConfirm: (schema: DataSchema) => void;
  onBack: () => void;
}

export default function SchemaEditor({ schema, onConfirm, onBack }: SchemaEditorProps) {
  const [editedSchema, setEditedSchema] = useState(schema);

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold mb-4">Review & Edit Schema</h3>
        <p className="text-gray-600 mb-6">
          Review the AI-inferred schema and make any necessary adjustments before generation.
        </p>
      </div>

      <div className="space-y-4">
        {editedSchema.columns.map((col, idx) => (
          <div key={idx} className="p-4 border rounded-lg bg-gray-50">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Column Name
                </label>
                <input
                  type="text"
                  value={col.name}
                  onChange={(e) => {
                    const newCols = [...editedSchema.columns];
                    newCols[idx].name = e.target.value;
                    setEditedSchema({ ...editedSchema, columns: newCols });
                  }}
                  className="w-full px-3 py-2 border rounded"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Type
                </label>
                <select
                  value={col.type}
                  className="w-full px-3 py-2 border rounded"
                >
                  <option value="string">String</option>
                  <option value="integer">Integer</option>
                  <option value="float">Float</option>
                  <option value="boolean">Boolean</option>
                  <option value="datetime">DateTime</option>
                  <option value="email">Email</option>
                </select>
              </div>
            </div>
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Description
              </label>
              <textarea
                value={col.description}
                onChange={(e) => {
                  const newCols = [...editedSchema.columns];
                  newCols[idx].description = e.target.value;
                  setEditedSchema({ ...editedSchema, columns: newCols });
                }}
                className="w-full px-3 py-2 border rounded"
                rows={2}
              />
            </div>
          </div>
        ))}
      </div>

      <div className="flex justify-between gap-4">
        <button
          onClick={onBack}
          className="px-6 py-3 border rounded-lg hover:bg-gray-50"
        >
          Back
        </button>
        <button
          onClick={() => onConfirm(editedSchema)}
          className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
        >
          Confirm Schema
        </button>
      </div>
    </div>
  );
}
