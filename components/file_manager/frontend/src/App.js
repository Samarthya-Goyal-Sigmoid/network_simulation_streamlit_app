import logo from './logo.svg';
import './App.css';

function App() {
  return (
    <div className="upload-container">
      <button className="upload-button" onClick={handleClick}>
        <img src={UploadIcon} alt="Upload" style={{ width: '24px', height: '24px' }} />
      </button>
    </div>
  );
}

export default App;
