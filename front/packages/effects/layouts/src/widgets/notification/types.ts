interface NotificationItem {
  id: string;
  avatar: string;
  date: string;
  isRead?: boolean;
  message: string;
  title: string;
  actionUrl?: string;
}

export type { NotificationItem };
