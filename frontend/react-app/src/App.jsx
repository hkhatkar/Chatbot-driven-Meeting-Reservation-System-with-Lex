// frontend/react-app/src/App.jsx
import React, { useState, useEffect } from "react"
import { Amplify} from "aws-amplify"
import { Interactions } from "@aws-amplify/interactions"
import awsConfig from "./aws-exports"

Amplify.configure({
  Auth: { region: awsConfig.lexBotRegion },
  Interactions: {
    bots: {
      [awsConfig.lexBotName]: {
        name: awsConfig.lexBotName,
        aliasId: "$LATEST",
        region: awsConfig.lexBotRegion
      }
    }
  }
})

export default function App() {
  // Bookings
  const [bookings, setBookings] = useState([])
  useEffect(() => {
    fetchBookings()
    const iv = setInterval(fetchBookings, 30000)
    return () => clearInterval(iv)
  }, [])

  async function fetchBookings() {
    try {
      const res = await fetch(awsConfig.bookingApiUrl)
      if (!res.ok) throw new Error(res.statusText)
      setBookings(await res.json())
    } catch (e) {
      console.error("Failed to load bookings:", e)
    }
  }

  // Chat
  const [chatLogs, setChatLogs] = useState([
    { from: "bot", text: "Hello! Ask me to book or check a room." }
  ])
  const [chatInput, setChatInput] = useState("")

  async function sendToBot() {
    if (!chatInput.trim()) return
    setChatLogs(logs => [...logs, { from: "you", text: chatInput }])
    try {
      const res = await Interactions.send(awsConfig.lexBotName, chatInput)
      setChatLogs(logs => [...logs, { from: "bot", text: res.message }])
    } catch (err) {
      console.error(err)
      setChatLogs(logs => [...logs, { from: "bot", text: "Error talking to bot." }])
    }
    setChatInput("")
  }

  return (
    <div className="grid grid-cols-3 h-screen">
      {/* Center: Bookings */}
      <div className="col-span-2 overflow-auto p-4">
        <h1 className="text-2xl mb-4">Current Bookings</h1>
        <table className="min-w-full table-auto">
          <thead>
            <tr>
              <th>Room</th>
              <th>Date</th>
              <th>Time</th>
              <th>Attendees</th>
            </tr>
          </thead>
          <tbody>
            {bookings.map(b => (
              <tr key={b.id} className="border-t">
                <td>{b.room_id}</td>
                <td>{b.date}</td>
                <td>{b.start_time}–{b.end_time}</td>
                <td>{b.attendees.join(", ")}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Right: Chat */}
      <aside className="col-span-1 border-l p-4 flex flex-col">
        <h2 className="text-xl mb-2">Meeting Bot</h2>
        <div className="flex-1 overflow-auto mb-2 space-y-2">
          {chatLogs.map((m,i) => (
            <div
              key={i}
              className={`p-2 rounded ${
                m.from==="bot" ? "bg-gray-100 self-start" : "bg-blue-100 self-end"
              } max-w-xs`}
            >
              <strong>{m.from==="bot" ? "Bot" : "You"}:</strong> {m.text}
            </div>
          ))}
        </div>
        <div className="mt-auto flex">
          <input
            className="flex-1 p-2 border rounded-l"
            value={chatInput}
            onChange={e => setChatInput(e.target.value)}
            onKeyDown={e => e.key==="Enter" && sendToBot()}
            placeholder="Type a message…"
          />
          <button
            className="px-4 bg-blue-600 text-white rounded-r"
            onClick={sendToBot}
          >
            Send
          </button>
        </div>
      </aside>
    </div>
  )
}
