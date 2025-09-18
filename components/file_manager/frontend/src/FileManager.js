import React, { useEffect } from "react";
import { Streamlit } from "streamlit-component-lib";
import UploadIcon from "./assets/UploadIcon.svg";

const FileUploader = () => {
  useEffect(() => {
    Streamlit.setComponentReady();
    Streamlit.setFrameHeight(40);
  }, []);

  const sendToStreamlit = (type, payload = {}) => {
    Streamlit.setComponentValue({ type, ...payload });
  };

  const handleUpload = () => {
    const input = document.createElement("input");
    input.type = "file";
    input.onchange = (e) => {
      const file = e.target.files[0];
      if (file) {
        const reader = new FileReader();
        reader.onload = () => {
          const data = reader.result;
          sendToStreamlit("upload", {
            filename: file.name,
            content: data.split(",")[1],
          });
        };
        reader.readAsDataURL(file);
      }
    };
    input.click();
  };

  return (
    <div style={styles.container}>
      <button style={styles.iconButton} onClick={handleUpload} title="Upload">
        <UploadIcon width={25} height={30} />
      </button>
    </div>
  );
};

const styles = {
  container: {
    display: "flex",
    borderRadius: "8px",
    background: "white",
    justifyContent: "center",
    alignItems: "center",
    width: "fit-content",
    margin: "-7px "
  },
  iconButton: {
    background: "white",
    border: "1px solid rgb(49, 51, 63)",
    borderRadius: "8px",
    fontSize: "20px",
    cursor: "pointer",
    color: "black",
    transition: "color 0.2s",
  },
};

export default FileUploader;