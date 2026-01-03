# Fixing "Phone numbers from this country are currently not supported"

This error comes directly from **Clerk's Configuration**, not the code. Development instances of Clerk often have restrictions on SMS delivery to certain countries (like India) to prevent spam/abuse, or simply because it requires enabling paid plans or specific settings.

### Solution 1: Use Email or Google (Recommended for Dev)
The easiest fix is to simply **sign up using an Email Address or Google Account** instead of a phone number. The code has been updated to show a hint for this.

### Solution 2: Change Clerk Settings
If you *must* use phone numbers, you need to change your configuration in the Clerk Dashboard:

1.  Go to **[Clerk Dashboard](https://dashboard.clerk.com/)**.
2.  Select your application.
3.  Go to **User & Authentication > Email, Phone, Username**.
4.  Look at the **Phone Number** settings.
    *   Ensure **SMS** is enabled properly (check for any warnings).
    *   You might need to enable specific countries in the **Restrictions** or **SMS Vendor** settings if available.
5.  *Alternatively*: **Disable Phone Number** as a required field and enable **Email Address** as the primary identifier to prevent users from accidentally trying to use phone numbers that won't work.

### Recommended "Email Only" Setup for Dev:
1.  Turn **OFF** Phone Number.
2.  Turn **ON** Email Address.
3.  Turn **ON** Google (Social Connection).
