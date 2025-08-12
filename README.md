# Facilities Management AI Agent

A **voice-enabled customer service AI agent** for facilities management that handles service requests, schedules appointments, and manages emergencies through natural conversation or text chat.

## 🏗️ Architecture

**Backend (Python/FastAPI):**
- **Agent Framework:** Google ADK (Agent Development Kit) with Live API
- **Model:** Gemini 2.0 Flash Live (supports real-time voice conversation)
- **Data Layer:** CSV-based customer, facility, and technician data
- **Tools:** 20+ custom tools for booking, customer lookup, scheduling, emergency handling

**Frontend (HTMX + JavaScript):**
- **Base Framework:** HTMX for dynamic HTML updates and interactions
- **Voice Layer:** JavaScript + Web Audio API for real-time audio processing
- **Audio Processing:** AudioWorklet processors for PCM audio (16kHz input, 24kHz output)
- **Communication:** WebSocket streaming for bidirectional voice/text
- **UI:** Clean chat interface with voice call functionality

## ✨ Key Features

- 🎙️ **Voice Conversations:** Natural, interruptible speech using ADK Live API
- 📅 **Real Booking:** Checks technician availability, creates calendar appointments
- 🚨 **Emergency Handling:** Detects urgent keywords, escalates appropriately
- 📊 **Customer Data:** Looks up existing customers, service history
- 🔄 **Bidirectional Streaming:** Real-time audio/text communication via WebSocket

## 🚀 Quick Start with Docker

### Prerequisites
- Docker and Docker Compose installed
- Google Cloud credentials (see setup instructions below)
- Gemini API key (see setup instructions below)

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourcompany/facilities-ai-agent.git
   cd facilities-ai-agent
   ```

2. **Setup environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your actual API keys and credentials
   ```

3. **Add your credentials**
   - Place your `credentials.json` file in the project root
   - Ensure you have the required Google Cloud APIs enabled

4. **Build and run**
   ```bash
   docker-compose up --build
   ```

5. **Access the application**
   - Open http://localhost:8000 in your browser
   - Click "Start Call" to begin voice conversation

## 🔧 Development Setup

### Local Development (without Docker)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install dependencies
uv sync

# Run the application
uv run python -m app.main
```

### Hot Reload Development with Docker
```bash
# Use development compose file
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 🗂️ Project Structure

```
facilities-ai-agent/
├── app/
│   ├── agents/              # AI agent implementations
│   ├── data/               # CSV data files
│   ├── models/             # Data models
│   ├── services/           # Business logic services
│   ├── static/             # Frontend assets (CSS, JS, HTML)
│   ├── tools/              # Custom agent tools
│   ├── websocket/          # WebSocket handlers
│   └── main.py             # FastAPI application
├── Dockerfile              # Container configuration
├── docker-compose.yml      # Docker services
├── pyproject.toml          # Python dependencies
└── README.md              # This file
```

## 🔑 Required Credentials

### Gemini API Key
1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Add to your `.env` file as `GEMINI_API_KEY`

### Google Cloud Credentials
1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable the following APIs:
   - Calendar API
   - Gmail API
   - Cloud Speech-to-Text API (if using)
3. Create a service account and download `credentials.json`
4. Place in project root

### Email Configuration (if using Gmail integration)
1. Enable 2-factor authentication on your Gmail account
2. Generate an app password
3. Add credentials to `.env` file

## 📝 Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# Google Cloud
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials.json

# Email (optional)
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here

# Application
PORT=8000
```

## 🎯 Usage Example

**Typical conversation flow:**
1. User: *"Hi, I need AC maintenance"*
2. Agent identifies customer from voice/context
3. Agent checks technician availability
4. Agent books appointment
5. Agent creates Google Calendar event
6. Agent sends confirmation email

## 🛠️ Troubleshooting

### Common Issues

**Port conflicts:**
```bash
# Change port in docker-compose.yml
ports:
  - "8001:8000"  # Use different local port
```

**Permission errors:**
```bash
# Ensure credentials file is readable
chmod 644 credentials.json
```

**Audio issues:**
- Ensure microphone permissions are granted in browser
- Check that WebSocket connection is established
- Verify audio format compatibility (16kHz input, 24kHz output)

### Debugging
```bash
# View container logs
docker-compose logs -f facilities-ai-agent

# Access container shell
docker-compose exec facilities-ai-agent bash

# Check service status
docker-compose ps
```

## 🔒 Security Notes

- **Never commit** `.env` files or `credentials.json`
- Use environment-specific credentials for different deployments
- Regularly rotate API keys
- Monitor API usage and set appropriate limits

## 📊 Data Management

The application uses CSV files for data storage:
- `customers.csv` - Customer information and history
- `facilities.csv` - Building and facility details
- `technicians.csv` - Technician schedules and skills
- `availability.csv` - Real-time availability data
- `work_orders.csv` - Service requests and status

**Data Persistence:** With Docker volumes, changes to these files persist between container restarts.

## 🤝 Contributing

1. Create a feature branch
2. Make your changes
3. Test with Docker: `docker-compose up --build`
4. Submit a pull request

## 📞 Support

For technical issues or questions:
- Check the troubleshooting section above
- Review container logs
- Contact the development team

---

**Technology Stack:** FastAPI + Google ADK + Gemini Live API + HTMX + WebSocket + Docker