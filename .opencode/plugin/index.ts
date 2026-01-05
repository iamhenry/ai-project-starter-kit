import type { Plugin } from "@opencode-ai/plugin"
import { platform } from "os"

export const NotifyPlugin: Plugin = async ({ client, $ }) => {
  return {
    async event(input) {
      if (input.event.type === "session.idle") {
        const sessionID = input.event.properties.sessionID
        
        let messageText = "Task Completed"
        
        try {
          // 1. Check if this is a main session or a subagent (child) session
          const sessionResult = await client.session.get({ 
            path: { id: sessionID } 
          })
          
          // If it has a parentID, it's a subagent. Skip notification.
          if (sessionResult.data && sessionResult.data.parentID) {
            return
          }

          // Fetch the session messages to find the last response
          const response = await client.session.messages({ 
            path: { id: sessionID }
          })
          
          if (response.data && response.data.length > 0) {
            // Get the last message
            const lastMessage = response.data[response.data.length - 1]
            
            // Only use assistant messages
            if (lastMessage.info.role === "assistant") {
              // Find the last text part
              // We cast to any because the type definition might be strict about the union
              const parts = lastMessage.parts as any[]
              const textParts = parts.filter(p => p.type === "text")
              
              if (textParts.length > 0) {
                const lastText = textParts[textParts.length - 1].text
                
                // Clean up the text: remove code blocks, newlines, extra spaces
                const cleanText = lastText
                  .replace(/```[\s\S]*?```/g, "") // Remove code blocks
                  .replace(/`[^`]*`/g, "")       // Remove inline code
                  .replace(/\n/g, " ")           // Replace newlines with spaces
                  .replace(/\s+/g, " ")          // Collapse spaces
                  .trim()
                
                // Take the first 5 words
                const words = cleanText.split(" ").filter(w => w.length > 0)
                if (words.length > 0) {
                  messageText = words.slice(0, 5).join(" ") + (words.length > 5 ? "..." : "")
                }
              }
            }
          }
        } catch (e) {
          // console.error("Error fetching messages:", e)
        }

        const currentPlatform = platform()
        const title = "OpenCode"
        
        try {
          switch (currentPlatform) {
            case "darwin": // macOS
              await $`osascript -e 'display notification "${messageText}" with title "${title}"'`
              break
              
            case "linux": // Linux
              // Check for WSL
              try {
                const version = await $`cat /proc/version`.text()
                if (version.toLowerCase().includes("microsoft")) {
                  // WSL - PowerShell fallback
                  // Escape quotes for PowerShell
                  const safeMsg = messageText.replace(/'/g, "''").replace(/"/g, '\\"')
                  await $`powershell.exe -Command "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.MessageBox]::Show('${safeMsg}', '${title}')"`
                  break
                }
              } catch (e) {}
              
              // Standard Linux
              await $`notify-send "${title}" "${messageText}" --icon=dialog-information`
              break
              
            case "win32": // Windows
              try {
                const safeMsg = messageText.replace(/'/g, "''")
                await $`powershell -Command "New-BurntToastNotification -Text '${title}', '${safeMsg}'"`
              } catch {
                await $`msg * "${title}: ${messageText}"`
              }
              break
          }
        } catch (error) {
          // Fail silently
        }
      }
    },
  }
}
