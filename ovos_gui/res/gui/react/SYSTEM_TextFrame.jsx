import React from "react";
import { ContentElement } from "CORE/utils";

function RenderPage(props) {
	const skill_props = props.skillState;
	console.log(skill_props)
	return (
		<div className="h-aligned-container text-center"
			 style={{justifyContent: "center",
				     alignItems: "center",
			 		 left: "1%",
			         right: "1%"}}>
            <ContentElement
				elementType={"TextFrame"}
				id={"title"}
				className={"col-12 h1"}
				text={skill_props.title}
				display={skill_props.display}
				duration={15000}
				// TODO: duration from config
			/>
			<ContentElement
				elementType={"TextFrame"}
				id={"text"}
				className={"col-12 h3"}
				text={skill_props.text}
				display={skill_props.display}
				duration={150000}
				// TODO: duration from config
			/>
		</div>
	);
}

export default RenderPage