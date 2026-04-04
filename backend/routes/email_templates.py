# flake8: noqa: E501
"""HTML + plain-text email templates for transactional emails."""


def verification_email(greeting: str, verify_url: str, base_url: str) -> tuple[str, str]:
    """Returns (html, text) for the email verification email."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:40px 20px;background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
    <div style="background:#0f172a;padding:32px 40px;text-align:center;">
      <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">Ron<span style="color:#6366f1;">.</span>dev</span>
    </div>
    <div style="padding:40px 40px 32px;">
      <h1 style="font-size:22px;font-weight:700;color:#0f172a;margin:0 0 12px;">Verify your email address</h1>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 16px;">{greeting}</p>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 16px;">Thanks for signing up! Click the button below to verify your email address and activate your account.</p>
      <div style="text-align:center;margin:32px 0;">
        <a href="{verify_url}" style="display:inline-block;background:#6366f1;color:#ffffff;text-decoration:none;font-size:15px;font-weight:600;padding:14px 36px;border-radius:8px;">Verify my email</a>
      </div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;font-size:13px;color:#64748b;">
        <strong style="color:#0f172a;">This link expires in 24 hours.</strong> If you didn't create an account, you can safely ignore this email.
      </div>
      <p style="margin-top:24px;font-size:13px;color:#94a3b8;">Button not working? Copy and paste this link into your browser:<br>
        <a href="{verify_url}" style="color:#6366f1;word-break:break-all;">{verify_url}</a>
      </p>
    </div>
    <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:24px 40px;text-align:center;font-size:12px;color:#94a3b8;line-height:1.6;">
      You're receiving this because you signed up at <a href="{base_url}" style="color:#6366f1;text-decoration:none;">Ron's Portfolio</a>.<br>
      &copy; 2026 Ron Harifiyati
    </div>
  </div>
</body>
</html>"""
    text = (
        f"{greeting}\n\n"
        "Thanks for signing up! Verify your email address by visiting:\n"
        f"{verify_url}\n\n"
        "This link expires in 24 hours. If you didn't create an account, ignore this email.\n\n"
        "\u00a9 2026 Ron Harifiyati"
    )
    return html, text


def reset_email(greeting: str, reset_url: str, base_url: str) -> tuple[str, str]:
    """Returns (html, text) for the password reset email."""
    html = f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:40px 20px;background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;">
  <div style="max-width:560px;margin:0 auto;background:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 24px rgba(0,0,0,0.08);">
    <div style="background:#0f172a;padding:32px 40px;text-align:center;">
      <span style="font-size:22px;font-weight:700;color:#ffffff;letter-spacing:-0.5px;">Ron<span style="color:#6366f1;">.</span>dev</span>
    </div>
    <div style="padding:40px 40px 32px;">
      <h1 style="font-size:22px;font-weight:700;color:#0f172a;margin:0 0 12px;">Reset your password</h1>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 16px;">{greeting}</p>
      <p style="font-size:15px;color:#475569;line-height:1.6;margin:0 0 16px;">We received a request to reset your password. Click the button below to choose a new one.</p>
      <div style="text-align:center;margin:32px 0;">
        <a href="{reset_url}" style="display:inline-block;background:#6366f1;color:#ffffff;text-decoration:none;font-size:15px;font-weight:600;padding:14px 36px;border-radius:8px;">Reset my password</a>
      </div>
      <div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:12px 16px;font-size:13px;color:#64748b;">
        <strong style="color:#0f172a;">This link expires in 1 hour.</strong> If you didn't request a password reset, you can safely ignore this email &mdash; your password won't change.
      </div>
      <p style="margin-top:24px;font-size:13px;color:#94a3b8;">Button not working? Copy and paste this link into your browser:<br>
        <a href="{reset_url}" style="color:#6366f1;word-break:break-all;">{reset_url}</a>
      </p>
    </div>
    <div style="background:#f8fafc;border-top:1px solid #e2e8f0;padding:24px 40px;text-align:center;font-size:12px;color:#94a3b8;line-height:1.6;">
      You're receiving this because a password reset was requested for your account at <a href="{base_url}" style="color:#6366f1;text-decoration:none;">Ron's Portfolio</a>.<br>
      &copy; 2026 Ron Harifiyati
    </div>
  </div>
</body>
</html>"""
    text = (
        f"{greeting}\n\n"
        "We received a request to reset your password. Visit this link to choose a new one:\n"
        f"{reset_url}\n\n"
        "This link expires in 1 hour. If you didn't request this, ignore this email.\n\n"
        "\u00a9 2026 Ron Harifiyati"
    )
    return html, text
