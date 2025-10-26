# SEMA-JOIN Frontend


## Structure

```
frontend/
├── app/
│   ├── page.tsx              # Main app logic
│   ├── page.module.css       # Page styles
│   ├── layout.tsx            # Root layout
│   └── globals.css           # Global styles
├── components/
│   ├── Header.tsx            # App header
│   ├── ErrorAlert.tsx        # Error display
│   ├── TableUploadPanel.tsx  # File upload + table
│   ├── InteractiveDataTable.tsx # Clickable table
│   ├── DataTable.tsx         # Simple table
│   ├── BridgeTablePanel.tsx  # Bridge table section
│   ├── JoinResultPanel.tsx   # Results section
│   ├── TableModal.tsx        # Full table modal
│   └── *.module.css          # Component styles
├── lib/
│   └── api.ts                # API client
└── public/
    ├── d2ip_logo.png
    ├── sample_table_r.json
    └── sample_table_s.json
```

## Getting Started

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment (Optional)

The frontend connects to `http://localhost:8000` by default.

If your backend runs on a different URL, create `.env.local`:

```env
NEXT_PUBLIC_API_URL=http://your-backend-url:port
```

## Tech Stack

- Next.js 16
- React 19
- TypeScript
- CSS Modules
- Tailwind CSS v4
