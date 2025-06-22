import React, { useState, useEffect, useContext } from "react";
import { Interactions } from "aws-amplify";
import { ConfigContext } from "./ConfigContext";

export default function App() {
  const awsConfig = useContext(ConfigContext);

  // Bookings state
  const [bookings, setBookings] = useState([]);

  useEffect(() => {
    fetchBookings();
    const iv = setInterval(fetchBookings, 30000);
    return () => clearInterval(iv);
  }, []);

  async function fetchBookings() {
    try {
      const res = await fetch(`${awsConfig.bookingApiUrl}bookings`);
      if (!res.ok) throw new Error(res.statusText);
      setBookings(await res.json());
    } catch (e) {
      console.error("Failed to load bookings:", e);
    }
  }

  // Chat state
  const [chatLogs, setChatLogs] = useState([
    { from: "bot", text: "Hello! Ask me to book or check a room." }
  ]);
  const [chatInput, setChatInput] = useState("");

  async function sendToBot() {
    if (!chatInput.trim()) return;
    setChatLogs((logs) => [...logs, { from: "you", text: chatInput }]);
    try {
      const res = await Interactions.send(awsConfig.lexBotName, chatInput);
      console.log("Lex raw response:", res);
      if (res.messages && res.messages.length) {
        res.messages.forEach((m) => {
          setChatLogs((logs) => [...logs, { from: "bot", text: m.content }]);
        });
      } else {
        setChatLogs((logs) => [...logs, { from: "bot", text: "[No message from bot]" }]);
      }
    } catch (err) {
      console.error(err);
      setChatLogs((logs) => [...logs, { from: "bot", text: "Error talking to bot." }]);
    }
    setChatInput("");
  }

  return (
    <div className="h-screen grid grid-cols-1 md:grid-cols-3 gap-4 bg-gray-50 p-4">
      {/* Bookings Panel */}
      <section className="md:col-span-2 bg-white shadow-lg rounded-xl flex flex-col overflow-hidden">
        <header className="px-6 py-4 border-b">
          <h1 className="text-2xl font-semibold text-gray-800">Current Bookings</h1>
        </header>
        <div className="p-4 flex-1 overflow-y-auto">
          <table className="min-w-full table-auto">
            <thead className="bg-gray-100 sticky top-0">
              <tr>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Room</th>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Date</th>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Time</th>
                <th className="px-4 py-2 text-left text-sm font-medium text-gray-600">Attendees</th>
              </tr>
            </thead>
            <tbody>
              {bookings.map((b) => (
                <tr key={b.id} className="border-b hover:bg-gray-50">
                  <td className="px-4 py-2 text-gray-700">{b.room_id}</td>
                  <td className="px-4 py-2 text-gray-700">{b.date}</td>
                  <td className="px-4 py-2 text-gray-700">{b.start_time}–{b.end_time}</td>
                  <td className="px-4 py-2 text-gray-700">{b.attendees.join(", ")}</td>
                </tr>
              ))}
            </tbody>
          </table>
          {bookings.length === 0 && (
            <div className="text-center text-gray-500 mt-8">No bookings found.</div>
          )}
        </div>
      </section>

      {/* Chat Panel */}
      <aside className="bg-white shadow-lg rounded-xl flex flex-col overflow-hidden">
        <header className="px-6 py-4 border-b">
          <h2 className="text-xl font-semibold text-gray-800">Meeting Bot</h2>
        </header>
        <div className="flex-1 p-4 overflow-y-auto space-y-4">
          {chatLogs.map((m, i) => (
            <div
              key={i}
              className={`max-w-xs p-3 rounded-2xl ${
                m.from === "bot" ? "bg-gray-100 self-start" : "bg-blue-100 self-end"
              }`}
            >
              <p className="text-sm">
                <strong className="capitalize">{m.from}:</strong> {m.text}
              </p>
            </div>
          ))}
        </div>
        <div className="px-4 py-3 border-t flex">
          <input
            className="flex-1 px-4 py-2 border rounded-l-lg focus:outline-none"
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && sendToBot()}
            placeholder="Type a message…"
          />
          <button
            className="px-6 bg-blue-600 text-white font-medium rounded-r-lg hover:bg-blue-700 transition"
            onClick={sendToBot}
          >
            Send
          </button>
        </div>
      </aside>
    </div>
  );
}
