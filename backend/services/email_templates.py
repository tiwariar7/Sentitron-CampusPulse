"""
Jinja2-rendered HTML email templates.
All templates share a common base layout (inline CSS for email client compat).
"""

SEVERITY_COLORS = {
    "CRITICAL": "#dc2626",
    "HIGH":     "#ea580c",
    "WARNING":  "#d97706",
    "INFO":     "#2563eb",
}

BASE_STYLE = """
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #0f0f1a; margin: 0; padding: 0; }
  .wrapper { max-width: 640px; margin: 32px auto; background: #1a1a2e; border-radius: 12px;
             border: 1px solid #2a2a4a; overflow: hidden; }
  .header  { padding: 24px 32px; background: linear-gradient(135deg, #1e1b4b, #312e81); }
  .header h1 { margin: 0; color: #c7d2fe; font-size: 20px; font-weight: 700; letter-spacing: 0.5px; }
  .header p  { margin: 4px 0 0; color: #818cf8; font-size: 13px; }
  .body    { padding: 28px 32px; color: #e2e8f0; }
  .badge   { display: inline-block; padding: 4px 12px; border-radius: 9999px;
             font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; }
  .field   { margin: 12px 0; }
  .label   { color: #94a3b8; font-size: 12px; text-transform: uppercase; letter-spacing: 0.5px; }
  .value   { color: #f1f5f9; font-size: 15px; margin-top: 2px; }
  .divider { border: none; border-top: 1px solid #2a2a4a; margin: 20px 0; }
  .cta     { display: inline-block; margin-top: 20px; padding: 12px 28px;
             background: #4f46e5; color: #fff; text-decoration: none;
             border-radius: 8px; font-weight: 600; font-size: 14px; }
  .footer  { padding: 16px 32px; background: #13131f; color: #475569; font-size: 11px; }
  table    { width: 100%; border-collapse: collapse; }
  th       { text-align: left; color: #94a3b8; font-size: 11px; text-transform: uppercase;
             padding: 8px 12px; border-bottom: 1px solid #2a2a4a; }
  td       { padding: 10px 12px; color: #e2e8f0; font-size: 13px;
             border-bottom: 1px solid #1e1e3a; vertical-align: top; }
"""


def _base_html(title: str, body_content: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{title}</title>
  <style>{BASE_STYLE}</style>
</head>
<body>
  <div class="wrapper">
    <div class="header">
      <h1>🎓 Sentitron CampusPulse</h1>
      <p>Real-Time AI Campus Intelligence & Escalation Platform</p>
    </div>
    <div class="body">
      {body_content}
    </div>
    <div class="footer">
      This is an automated alert from Sentitron CampusPulse.
      Do not reply to this email. &nbsp;|&nbsp;
      Powered by Sentitron AI &copy; 2026
    </div>
  </div>
</body>
</html>"""


def render_escalation_alert(
    complaint_id: str,
    department: str,
    severity: str,
    description: str,
) -> str:
    color = SEVERITY_COLORS.get(severity.upper(), "#6366f1")
    body = f"""
      <h2 style="margin:0 0 16px; color:#f1f5f9;">Incident Escalation Alert</h2>
      <span class="badge" style="background:{color}20; color:{color}; border:1px solid {color}40;">
        {severity.upper()}
      </span>
      <hr class="divider">
      <div class="field">
        <div class="label">Complaint ID</div>
        <div class="value" style="font-family:monospace; font-size:16px; color:#818cf8;">{complaint_id}</div>
      </div>
      <div class="field">
        <div class="label">Department</div>
        <div class="value">{department}</div>
      </div>
      <div class="field">
        <div class="label">Description</div>
        <div class="value" style="line-height:1.6;">{description}</div>
      </div>
      <hr class="divider">
      <p style="color:#94a3b8; font-size:13px;">
        This incident has been automatically escalated based on severity thresholds.
        Please review and take appropriate action immediately.
      </p>
      <a href="http://localhost:3000/incidents" class="cta">View Incident Dashboard →</a>
    """
    return _base_html(f"[ESCALATION] {complaint_id}", body)


def render_notification_digest(notifications: list) -> str:
    rows = ""
    for n in notifications:
        sev   = n.get("severity", "INFO")
        color = SEVERITY_COLORS.get(sev, "#6366f1")
        badge = (
            f'<span class="badge" style="background:{color}20;color:{color};'
            f'border:1px solid {color}40; font-size:10px;">{sev}</span>'
        )
        rows += f"""
          <tr>
            <td>{badge}</td>
            <td>{n.get('title', '')}</td>
            <td>{n.get('message', '')[:80]}...</td>
            <td>{n.get('lifecycle_state', '')}</td>
            <td style="color:#64748b;">{n.get('timestamp', '')[:10]}</td>
          </tr>
        """

    body = f"""
      <h2 style="margin:0 0 16px; color:#f1f5f9;">Notification Digest</h2>
      <p style="color:#94a3b8; font-size:13px;">{len(notifications)} notification(s) requiring your attention.</p>
      <hr class="divider">
      <table>
        <thead>
          <tr>
            <th>Severity</th><th>Title</th><th>Message</th><th>State</th><th>Date</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <a href="http://localhost:3000/notifications" class="cta">View All Notifications →</a>
    """
    return _base_html("CampusPulse Notification Digest", body)


def render_system_alert(alert_name: str, severity: str, description: str) -> str:
    color = SEVERITY_COLORS.get(severity.upper(), "#6366f1")
    body = f"""
      <h2 style="margin:0 0 16px; color:#f1f5f9;">System Alert</h2>
      <span class="badge" style="background:{color}20; color:{color}; border:1px solid {color}40;">
        {severity.upper()}
      </span>
      <hr class="divider">
      <div class="field">
        <div class="label">Alert Name</div>
        <div class="value">{alert_name}</div>
      </div>
      <div class="field">
        <div class="label">Description</div>
        <div class="value">{description}</div>
      </div>
      <hr class="divider">
      <a href="http://localhost:9090" class="cta">View Prometheus →</a>
      &nbsp;&nbsp;
      <a href="http://localhost:3001" class="cta" style="background:#059669;">Open Grafana →</a>
    """
    return _base_html(f"[SYSTEM] {alert_name}", body)
