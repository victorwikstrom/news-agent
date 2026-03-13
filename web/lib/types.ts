export type Channel = "email" | "slack";

export type Source = {
  id: string;
  name: string;
  category: string;
};

export type Subscription = {
  id: string;
  user_id: string;
  channel: Channel;
  email: string | null;
  slack_webhook_url: string | null;
  digest_time: string;
  timezone: string;
  weekdays_only: boolean;
  created_at: string;
  updated_at: string;
};

export type SubscriptionPayload = {
  channel: Channel;
  email?: string;
  slack_webhook_url?: string;
  digest_time: string;
  timezone: string;
  weekdays_only: boolean;
  source_ids: string[];
};
