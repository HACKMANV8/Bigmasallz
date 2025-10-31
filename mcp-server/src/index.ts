#!/usr/bin/env node

/**
 * SynthAIx MCP Server
 * 
 * Uses GitHub Copilot agent as the data generation engine.
 * This MCP server exposes tools that leverage Copilot's capabilities
 * to generate synthetic data without API rate limits.
 */

import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  Tool,
} from '@modelcontextprotocol/sdk/types.js';
import { z } from 'zod';

// Schema definitions for validation
const SchemaFieldSchema = z.object({
  name: z.string(),
  type: z.string(),
  description: z.string().optional(),
  constraints: z.record(z.any()).optional(),
});

const DataSchemaSchema = z.object({
  fields: z.array(SchemaFieldSchema),
  metadata: z.record(z.any()).optional(),
});

const GenerateDataRequestSchema = z.object({
  schema: DataSchemaSchema,
  num_rows: z.number().min(1).max(1000),
  chunk_id: z.string().optional(),
  enable_deduplication: z.boolean().optional().default(false),
});

const TranslateSchemaRequestSchema = z.object({
  prompt: z.string().min(1),
});

// Server state
interface ServerState {
  generatedData: Map<string, any[]>;
  deduplicationCache: Set<string>;
}

const state: ServerState = {
  generatedData: new Map(),
  deduplicationCache: new Set(),
};

// Helper function to create hash for deduplication
function hashObject(obj: any): string {
  return JSON.stringify(obj, Object.keys(obj).sort());
}

// MCP Server setup
const server = new Server(
  {
    name: 'synthaix-mcp-server',
    version: '1.0.0',
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

/**
 * Tool: translate_schema
 * 
 * Converts natural language prompt to structured data schema.
 * GitHub Copilot will infer the appropriate schema structure.
 */
const translateSchemaTool: Tool = {
  name: 'translate_schema',
  description: 'Convert a natural language description into a structured JSON schema for data generation. GitHub Copilot will analyze the prompt and create appropriate field definitions.',
  inputSchema: {
    type: 'object',
    properties: {
      prompt: {
        type: 'string',
        description: 'Natural language description of the data to generate (e.g., "user data with name, email, and age")',
      },
    },
    required: ['prompt'],
  },
};

/**
 * Tool: generate_data_chunk
 * 
 * Generates a chunk of synthetic data based on schema.
 * GitHub Copilot will create realistic, diverse data.
 */
const generateDataChunkTool: Tool = {
  name: 'generate_data_chunk',
  description: 'Generate synthetic data rows based on a provided schema. GitHub Copilot will create realistic, diverse data that follows all field constraints. This is the PRIMARY data generation tool - use this to create datasets.',
  inputSchema: {
    type: 'object',
    properties: {
      schema: {
        type: 'object',
        description: 'Data schema with fields array',
        properties: {
          fields: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                name: { type: 'string' },
                type: { type: 'string' },
                description: { type: 'string' },
                constraints: { type: 'object' },
              },
            },
          },
        },
      },
      num_rows: {
        type: 'number',
        description: 'Number of rows to generate (1-1000)',
        minimum: 1,
        maximum: 1000,
      },
      chunk_id: {
        type: 'string',
        description: 'Optional unique identifier for this chunk',
      },
      enable_deduplication: {
        type: 'boolean',
        description: 'Whether to check and remove duplicates',
        default: false,
      },
    },
    required: ['schema', 'num_rows'],
  },
};

/**
 * Tool: check_duplicates
 * 
 * Check if generated data contains duplicates.
 */
const checkDuplicatesTool: Tool = {
  name: 'check_duplicates',
  description: 'Check a set of data rows for duplicates and return only unique rows',
  inputSchema: {
    type: 'object',
    properties: {
      data: {
        type: 'array',
        description: 'Array of data objects to check',
      },
    },
    required: ['data'],
  },
};

// Register tools
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      translateSchemaTool,
      generateDataChunkTool,
      checkDuplicatesTool,
    ],
  };
});

// Handle tool calls
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    if (name === 'translate_schema') {
      // Validate input
      const validated = TranslateSchemaRequestSchema.parse(args);
      const { prompt } = validated;

      // Return a structured response that tells Copilot to generate the schema
      return {
        content: [
          {
            type: 'text',
            text: `I need to analyze this prompt and create a data schema: "${prompt}"

Please analyze this prompt and generate a JSON schema with the following structure:
{
  "fields": [
    {
      "name": "field_name",
      "type": "string|integer|float|boolean|date|email|phone|uuid",
      "description": "Description of the field",
      "constraints": {
        "min": value,
        "max": value,
        "options": ["choice1", "choice2"]
      }
    }
  ],
  "interpretation": "Your understanding of the user's request",
  "confidence": 0.95
}

Generate a complete schema that would produce realistic data for: "${prompt}"`,
          },
        ],
      };
    }

    if (name === 'generate_data_chunk') {
      // Validate input
      const validated = GenerateDataRequestSchema.parse(args);
      const { schema, num_rows, chunk_id, enable_deduplication } = validated;

      // Build a detailed prompt for Copilot to generate data
      const fieldDescriptions = schema.fields.map(field => {
        let desc = `- ${field.name} (${field.type})`;
        if (field.description) desc += `: ${field.description}`;
        if (field.constraints) {
          const constraints = Object.entries(field.constraints)
            .map(([k, v]) => `${k}=${JSON.stringify(v)}`)
            .join(', ');
          desc += ` [${constraints}]`;
        }
        return desc;
      }).join('\n');

      return {
        content: [
          {
            type: 'text',
            text: `GENERATE SYNTHETIC DATA

I need you to generate ${num_rows} rows of realistic, diverse synthetic data with the following schema:

${fieldDescriptions}

Requirements:
1. Return ONLY a valid JSON array of objects
2. Each object must have ALL fields from the schema
3. Values must be realistic and follow constraints
4. Data should be diverse and unique
5. Follow these type guidelines:
   - string: realistic text values
   - integer: whole numbers within constraints
   - float: decimal numbers within constraints
   - boolean: true or false
   - date: YYYY-MM-DD format
   - email: valid email format
   - phone: valid phone number format
   - uuid: valid UUID v4 format

Example format:
[
  {${schema.fields.map(f => `"${f.name}": <${f.type}_value>`).join(', ')}},
  ...${num_rows} total rows
]

${chunk_id ? `Chunk ID: ${chunk_id}` : ''}

Generate the data now as a JSON array:`,
          },
        ],
      };
    }

    if (name === 'check_duplicates') {
      const { data } = args as { data: any[] };

      if (!Array.isArray(data)) {
        throw new Error('Data must be an array');
      }

      // Simple hash-based deduplication
      const unique: any[] = [];
      const seen = new Set<string>();

      for (const row of data) {
        const hash = hashObject(row);
        if (!seen.has(hash)) {
          seen.add(hash);
          unique.push(row);
        }
      }

      const duplicatesRemoved = data.length - unique.length;

      return {
        content: [
          {
            type: 'text',
            text: JSON.stringify({
              unique_rows: unique,
              total_input: data.length,
              duplicates_removed: duplicatesRemoved,
              unique_count: unique.length,
            }, null, 2),
          },
        ],
      };
    }

    throw new Error(`Unknown tool: ${name}`);
  } catch (error) {
    const errorMessage = error instanceof Error ? error.message : String(error);
    return {
      content: [
        {
          type: 'text',
          text: `Error: ${errorMessage}`,
        },
      ],
      isError: true,
    };
  }
});

// Start server
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('SynthAIx MCP Server running on stdio');
}

main().catch((error) => {
  console.error('Server error:', error);
  process.exit(1);
});
