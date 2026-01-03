# Clerk Setup Instructions

To enable authentication, you must configure Clerk.

1.  **Create a Clerk Application**: Go to [https://dashboard.clerk.com/](https://dashboard.clerk.com/) and create a new application.
2.  **Get Keys**: Copy the `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` and `CLERK_SECRET_KEY` from the API Keys section.
3.  **Update Environment**:
    Create or update the `.env.local` file in this `frontend` directory with the following content:

    ```env
    NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_...
    CLERK_SECRET_KEY=sk_test_...
    NEXT_PUBLIC_CLERK_SIGN_IN_URL=/login
    NEXT_PUBLIC_CLERK_SIGN_UP_URL=/login
    ```

4.  **Restart Server**: If the server is running, restart it to load the new environment variables.
