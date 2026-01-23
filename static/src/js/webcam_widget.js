/** @odoo-module */

import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, useRef, onWillStart } from "@odoo/owl";

export class BenefitWebcamField extends Component {
    setup() {
        this.videoRef = useRef("video");
        this.videoRef = useRef("video");
        this.canvasRef = useRef("canvas");
        this.fileInputRef = useRef("fileInput");

        this.state = useState({
            isStreamActive: false,
            imgData: this.props.record.data[this.props.name] || null,
        });

        onWillStart(() => {
            // If we already have data, we might show it, but logic below handles it
        });
    }

    async startCamera() {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ video: true });
            this.videoRef.el.srcObject = stream;
            this.videoRef.el.play();
            this.state.isStreamActive = true;
            this.stream = stream;
            this.stream = stream;
        } catch (err) {
            console.error("Error accessing camera: ", err);
            let msg = "No se pudo acceder a la cámara.";
            if (window.isSecureContext === false) {
                msg += " El navegador bloquea el acceso a la cámara en conexiones no seguras (HTTP). Use HTTPS o localhost.";
            } else {
                msg += " Verifique permisos: " + err.message;
            }
            alert(msg);
        }
    }

    triggerFileUpload() {
        this.fileInputRef.el.click();
    }

    async onFileChange(ev) {
        const file = ev.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const result = e.target.result;
            const base64Data = result.split(',')[1];
            this.state.imgData = base64Data;
            this.props.record.update({ [this.props.name]: base64Data });
        };
        reader.readAsDataURL(file);

    }

    takePhoto() {
        const video = this.videoRef.el;
        const canvas = this.canvasRef.el;
        const context = canvas.getContext("2d");

        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        context.drawImage(video, 0, 0, canvas.width, canvas.height);

        // Get base64 string
        const dataURL = canvas.toDataURL("image/png");
        // Odoo Binary fields expect base64 without prefix usually, or we can just save it. 
        // Standard Odoo binary field usually strips 'data:image/png;base64,' but let's check.
        // Actually, the web client usually handles standard base64 content. 
        // We will strip the prefix to be safe as Odoo backend expects raw base64.
        const base64Data = dataURL.split(',')[1];

        this.state.imgData = base64Data;
        this.props.record.update({ [this.props.name]: base64Data });

        this.stopCamera();
    }

    stopCamera() {
        if (this.stream) {
            this.stream.getTracks().forEach(track => track.stop());
        }
        this.state.isStreamActive = false;
    }

    reset() {
        this.state.imgData = null;
        this.props.record.update({ [this.props.name]: false });
    }
}

BenefitWebcamField.template = "hr_benefit.WebcamField";
BenefitWebcamField.props = {
    ...standardFieldProps,
};
BenefitWebcamField.supportedTypes = ["binary"];

export const benefitWebcamField = {
    component: BenefitWebcamField,
    supportedTypes: ["binary"],
};

registry.category("fields").add("benefit_webcam", benefitWebcamField);
