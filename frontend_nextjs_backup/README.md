# SynthAIx Frontend

Next.js frontend for the SynthAIx synthetic data generation platform.

## Features

- **Natural Language Input**: Describe data in plain English
- **Schema Editor**: Review and edit AI-inferred schemas
- **Generation Configuration**: Configure workers, chunk size, and deduplication
- **Real-time Progress**: Live progress tracking with status updates
- **Results Viewer**: Preview and download generated data

## Installation

```bash
npm install
```

## Configuration

Create a `.env.local` file:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running

### Development

```bash
npm run dev
```

Visit http://localhost:3000

### Production Build

```bash
npm run build
npm start
```

### Docker

```bash
docker build -t synthaix-frontend .
docker run -p 3000:3000 synthaix-frontend
```

## Project Structure

```
frontend/
├── src/
│   ├── app/              # Next.js 14 App Router
│   ├── components/       # React components
│   │   ├── schema/       # Schema-related components
│   │   ├── generation/   # Generation components
│   │   └── ui/           # Shared UI components
│   ├── services/         # API service layer
│   ├── hooks/            # Custom React hooks
│   ├── types/            # TypeScript types
│   └── lib/              # Utilities
├── public/               # Static assets
└── tests/                # Test files
```

## Technology Stack

- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **HTTP Client**: Axios
- **Forms**: React Hook Form + Zod
- **Icons**: Lucide React

## License

MIT License
