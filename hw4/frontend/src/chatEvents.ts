// Window event that opens the chat panel from anywhere (e.g. "Ask about this item" on product pages).
export const OPEN_CHAT_EVENT = 'cc:open-chat'

export function openChat(): void {
  window.dispatchEvent(new Event(OPEN_CHAT_EVENT))
}
