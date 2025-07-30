import React, { useState, useEffect } from "react";
import io from 'socket.io-client';
import './App.css';

const socket = io('http://localhost:8000');

function App() {
  const [pictureStatus, setPictureStatus] = useState("");
  const [temp, setTemp] = useState("Loading...")
  const [light, setLight] = useState("Loading...")
  const [humidity, setHumidity] = useState("Loading...")
  const [ultrasonic, setUltrasonic] = useState("Loading...")
  const [message, setMessage] = useState("");

  const handleSend = () => {
    if (message.trim() !== "") {
      socket.emit("display", message);  // sending to backend
      setMessage("");  // clear input
    }
  }

  useEffect(() => {
    socket.on('connect', () => console.log('Connected:', socket.id));
    socket.on('temp', data => {
      console.log("Temp received")
      setTemp(data);
    });
    socket.on('light', data =>{
      console.log("Light received")
      setLight(data);
    });
    socket.on('humidity', data =>{
      console.log("Humidity received")
      setHumidity(data);
    });
    socket.on('ultrasonic', data =>{
      console.log("UltraSonic received")
      setUltrasonic(data);
    });
    return () => {
      socket.off('picture_taken');
      socket.off('temp');
      socket.off('light');
      socket.off('humiditu');
      socket.off('ultrasonic');
    };
  }, []);

  return (
    <div>
      {/* Live Sensor Dashboard Section */}
      <div style={{ padding: '2em' }}>
        <h1>Live Sensor Dashboard</h1>
        <p>Temp: {temp}°C</p>
        <p>Light: {light}</p>
        <p>Humidity: {humidity}</p>
        <p>Ultrasonic: {ultrasonic}cm</p>
      </div>

      {/* Message to Pico Section */}
      <div>
        <h1>Send Message to Pico</h1>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Type message"
        />
        <button onClick={handleSend}>Send</button>
      </div>

      {/* Image Section */}
      <div>
        <img src="/images/downloaded_image.jpg" alt="Downloaded image" />
      </div>
    </div>
  );
}

export default App;
